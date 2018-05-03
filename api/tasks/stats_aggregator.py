from __future__ import absolute_import, unicode_literals
from logging import Logger
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from celery import task
from api.models import Container
from django.db import OperationalError
import logging
import subprocess
import docker
import requests

# Get an instance of a logger
logger = logging.getLogger(__name__)  # type: Logger

@task()
def probe_per_sec():
    # Only CPU logging for now
    bulk = str(subprocess.check_output("docker stats --format '{{.Container}} {{.CPUPerc}}' --no-stream", shell=True))
    bulk_list = filter(None, bulk.split("\n"))
    # logger.info(bulk_list)
    for line in bulk_list:
        all_info = line.split()
        cont_id = all_info[0]
        cpu = all_info[1][:-1]
        # Lock access to db during transaction (safeguard against concurrent increments)
        with transaction.atomic():
            try:
                cont = Container.objects.select_for_update().get(cont_id=cont_id)
            except ObjectDoesNotExist:
                # Create container representation in the db if it does not exist
                cont = Container(cont_id=cont_id)
            cont.accu_cpu += float(cpu)
            cont.ticks += 1
            try:
                cont.save()
            except OperationalError:
                logger.warning("DB locked: concurrency avoided")
        # logger.info(cont.acu_cpu)
        # logger.info(cont.ticks)

@task()
def probe_per_interval():
    # Get docker client
    client = docker.from_env()
    # Get containers
    containers = client.containers.list()
    # Get Container stats & predict
    for container in containers:
        cont = Container.objects.get(cont_id=container.id[:12])
        port = subprocess.check_output(["docker port {0} | cut -d ':' -f 2".format(container.id)], shell=True)[:-1]
        get_url = "http://localhost:{0}/ca_tf/getLogs/".format(port)
        interval_info = requests.get(get_url)
        logger.info(interval_info.text)
        logger.info(interval_info.json())
        interval_info_dict = interval_info.json()
        cont.prev_subm = interval_info_dict['requests_submitted']
        cont.prev_rej = interval_info_dict['requests_rejected']
        cont.prev_fin = interval_info_dict['requests_finished']
        cont.prev_art = interval_info_dict['average_response_time']
        cont.predict_next_rr(sampling_interval=30)
        cont.print_logs(start_time)
        cont.save()
