from __future__ import absolute_import, unicode_literals
from logging import Logger
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from celery import task
from api.models import Container
from django.db import OperationalError
import logging
import subprocess
import gc


# Get an instance of a logger
logger = logging.getLogger(__name__)  # type: Logger


@task()
def probe_per_sec():
    print("persec")
    # Only CPU logging for now
    bulk = str(subprocess.check_output("docker stats --format '{{.Container}} {{.CPUPerc}}' --no-stream", shell=True))
    bulk_list = filter(None, bulk.split("\n"))
    for line in bulk_list:
        all_info = line.split()
        contid = all_info[0]
        cpu = all_info[1][:-1]
        # Lock access to db during transaction (safeguard against concurrent increments)
        with transaction.atomic():
            try:
                cont = Container.objects.select_for_update().get(cont_id=contid)
            # except ObjectDoesNotExist:
            except:
                # Create container representation in the db if it does not exist
                cont = Container(cont_id=contid)
		cont.app_id = int(str(subprocess.check_output("docker port %s" % contid, shell=True))[-2]) - 1
                # cont.assign_app_id() # -> deprecated
                cont.save()
                print ("Created container with id: " + str(cont.cont_id))
            cont.accu_cpu += float(cpu)
            cont.ticks += 1
	    print ("tick")
            try:
                cont.save()
            except OperationalError:
                print("DB locked: concurrency avoided")
	    print ("Container ticks: " + str(cont.ticks))
