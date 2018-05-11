from __future__ import absolute_import, unicode_literals
from logging import Logger
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from celery import task
from api.models import Container
from django.db import OperationalError
from django.conf import settings
import logging
import subprocess
import docker
import requests
import os


U_PES_MIN = settings.GLOBAL_SETTINGS['U_PES_MIN']
U_PES_MAX = settings.GLOBAL_SETTINGS['U_PES_MAX']
U_REQ_MIN = settings.GLOBAL_SETTINGS['U_REQ_MIN']
U_REQ_MAX = settings.GLOBAL_SETTINGS['U_REQ_MAX']
X_ART_REF = settings.GLOBAL_SETTINGS['X_ART_REF']
U_PES_REF = settings.GLOBAL_SETTINGS['U_PES_REF']
U_REQ_REF = settings.GLOBAL_SETTINGS['U_REQ_REF']
K1 = settings.GLOBAL_SETTINGS['K1']
K2 = settings.GLOBAL_SETTINGS['K2']
MAX_TOTAL_CONT_PES = settings.GLOBAL_SETTINGS['MAX_TOTAL_CONT_PES']
SAMPLING_INTERVAL = settings.GLOBAL_SETTINGS['SAMPLING_INTERVAL']


# Get an instance of a logger
logger = logging.getLogger(__name__)  # type: Logger

@task()
def probe_per_sec():
    logger.debug("persec")
    # Only CPU logging for now
    bulk = str(subprocess.check_output("docker stats --format '{{.Container}} {{.CPUPerc}}' --no-stream", shell=True))
    bulk_list = filter(None, bulk.split("\n"))
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
                cont.save()
            cont.accu_cpu += float(cpu)
            cont.ticks += 1
            try:
                cont.save()
            except OperationalError:
                print("DB locked: concurrency avoided")

@task()
def probe_per_interval():
    # Get docker client
    client = docker.from_env()
    # Get containers
    containers = client.containers.list()
    # Get Container stats, predict & scale
    for container in containers:
        cont = Container.objects.get(cont_id=container.id[:12])
        port = subprocess.check_output(["docker port {0} | cut -d ':' -f 2".format(container.id)], shell=True)[:-1]
        get_url = "http://localhost:{0}/ca_tf/getLogs/".format(port)
        interval_info = requests.get(get_url)
        print(interval_info.text)
        print(interval_info.json())
        interval_info_dict = interval_info.json()
        cont.prev_subm = interval_info_dict['requests_submitted']
        cont.prev_rej = interval_info_dict['requests_rejected']
        cont.prev_fin = interval_info_dict['requests_finished']
        cont.prev_art = interval_info_dict['average_response_time']
        cont.calc_cpu_usg()
        cont.predict_next_rr(SAMPLING_INTERVAL)
        cont.print_logs_and_csvs()
        cont.truncate()
        cont.save()
    scale()


def scale():
    total_pes = 0
    total_available_pes = int(subprocess.check_output("docker -D info | grep CPUs | sed 's/^CPUs: //'", shell=True))
    # Get docker client
    client = docker.from_env()
    # Get containers
    containers = client.containers.list()
    containers_ids = []
    # Remove "ghost" container records
    for container in containers:
        containers_ids.append(container.id[:12])
    Container.objects.exclude(cont_id__in=containers_ids).delete()
    # Calculate new operating conditions
    for container in containers:
        cont = Container.objects.get(cont_id=container.id[:12])
        print('Container ID: ' + cont.cont_id)
        print('Container Host: ' + str(cont.host_id))
        print('Container Operating Point: ' + str(cont.op_point))
        print('Container Previous Response Time: ' + str(cont.prev_art))
        # Models
        x0 = cont.prev_art
        op = cont.op_point
        app_id = cont.app_id
        pes_to_scale = K1[app_id][op] * (x0 - X_ART_REF[app_id][op]) + U_PES_REF[app_id][op]
        if pes_to_scale > U_PES_MAX[app_id][op]:
            pes_to_scale = U_PES_MAX[app_id][op]
        elif pes_to_scale < U_PES_MIN[app_id][op]:
            pes_to_scale = U_PES_MIN[app_id][op]
        cont.next_pes = pes_to_scale * total_available_pes
        print('PES to allocate to Container (%): ' + str(cont.next_pes))

        total_pes += cont.next_pes
        print('Total allocated PES of this Host (%): ' + str(total_pes))
        request_rate_upper_limit = K2[app_id][op] * (x0 - X_ART_REF[app_id][op]) + U_REQ_REF[app_id][op]
        if request_rate_upper_limit > U_REQ_MAX[app_id][op]:
            request_rate_upper_limit = U_REQ_MAX[app_id][op]
        elif request_rate_upper_limit < U_REQ_MIN[app_id][op]:
            request_rate_upper_limit = U_REQ_MIN[app_id][op]
        print('Request Rate Upper Limit for Container: ' + str(request_rate_upper_limit))
        cont.next_real_rr = request_rate_upper_limit
        cont.save()
    # PES normalization process
    if total_pes > MAX_TOTAL_CONT_PES * total_available_pes:
        for container in containers:
            cont = Container.objects.get(cont_id=container.id[:12])
            cont.next_pes = cont.next_pes * MAX_TOTAL_CONT_PES * total_available_pes / total_pes
            cont.save()
    # Perform actual scaling
    for container in containers:
        cont = Container.objects.get(cont_id=container.id[:12])
        # Get container/app port
        port = subprocess.check_output(["docker port {0} | cut -d ':' -f 2".format(container.id)], shell=True)[:-1]
        # Scale PES
        with open(os.devnull, 'wb') as devnull: # suppress output
            subprocess.check_call(["docker update --cpus=\"" + str(cont.next_pes*total_available_pes) + "\" " +
                                   str(container.id)], shell=True, stdout=devnull, stderr=subprocess.STDOUT)
        # Define upper request rate upper limit
        post_url = "http://localhost:{0}/ca_tf/serverInfo/".format(port)
        data_json = {'number': cont.next_real_rr*SAMPLING_INTERVAL}
        requests.post(post_url, json=data_json)
