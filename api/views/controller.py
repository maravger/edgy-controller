from django.core.exceptions import ObjectDoesNotExist
from celery import task
import docker
from api.models import Container
import logging
import os
import requests
import subprocess

U_PES_MIN = [[0, 0.10, 0.20, 0.30, 0.40], [0, 0.10, 0.20, 0.30, 0.40]]
U_PES_MAX = [[0, 0.30, 0.40, 0.50, 0.60], [0, 0.30, 0.40, 0.50, 0.60]]
U_REQ_MIN = [[0, 0.5, 3.5, 4.5, 5.5], [0, 0.5, 3.5, 4.5, 5.5]]
U_REQ_MAX = [[0, 3.5, 5.5, 7.5, 10], [0, 3.5, 5.5, 7.5, 10]]
X_ART_REF = [[0, 2.5, 2.5, 2.5, 2.5], [0, 3.5, 3.5, 3.5, 3.5]]
U_PES_REF = [[0, 0.25, 0.35, 0.45, 0.55], [0, 0.25, 0.35, 0.45, 0.55]]
U_REQ_REF = [[0, 2.9522, 4.6272, 6.1769, 8.0228], [0, 3.2358, 5.2899, 7.375, 9.5755]]
K1 = [[0, 0, 0, 0, 0.84874], [0, 1.4286, 0, 0, 0.61825]]
K2 = [[0, -0.21913, -0.34912, -0.52926, -0.79089], [0, -0.075496, -0.060028, -0.035707, -0.1213]]
MAX_TOTAL_CONT_PES = 1.00
INTERVAL = 30

logger = logging.getLogger(__name__)

# TODO: add redis installation to README

def scale():
    total_pes = 0
    total_available_pes = int(subprocess.check_output("docker -D info | grep CPUs | sed 's/^CPUs: //'", shell=True))
    # Get docker client
    client = docker.from_env()
    # Get containers
    containers = client.containers.list()
    # Calculate new operating conditions
    for container in containers:  # TODO: remove unused containers in db
        try:
            cont = Container.objects.get(cont_id=container.id[:12])
        except ObjectDoesNotExist:
            # Create container representation in the db if it does not exist
            cont = Container(cont_id=container.id[:12])
            cont.save()
        logger.info('Container ID: ' + cont.cont_id)
        logger.info('Container Host: ' + str(cont.host_id))
        logger.info('Container Operating Point: ' + str(cont.op_point))
        logger.info('Container Previous Response Time: ' + str(cont.prev_art))
        # Models
        x0 = cont.prev_art
        op = cont.op_point
        app_id = cont.app_id
        pes_to_scale = K1[app_id][op] * (x0 - X_ART_REF[app_id][op]) + U_PES_REF[app_id][op]
        if pes_to_scale > U_PES_MAX[app_id][op]:
            pes_to_scale = U_PES_MAX[app_id][op]
        elif pes_to_scale < U_PES_MIN[app_id][op]:
            pes_to_scale = U_PES_MIN[app_id][op]
        logger.info('PES to allocate to Container (%): ' + str(pes_to_scale))
        cont.next_pes = pes_to_scale

        total_pes += pes_to_scale
        logger.info('Total allocated PES of this Host (%): ' + str(pes_to_scale))
        request_rate_upper_limit = K2[app_id][op] * (x0 - X_ART_REF[app_id][op]) + U_REQ_REF[app_id][op]
        if request_rate_upper_limit > U_REQ_MAX[app_id][op]:
            request_rate_upper_limit = U_REQ_MAX[app_id][op]
        elif request_rate_upper_limit < U_REQ_MIN[app_id][op]:
            request_rate_upper_limit = U_REQ_MIN[app_id][op]
        logger.info('Request Rate Upper Limit for Container: ' + str(request_rate_upper_limit))
        cont.next_real_rr = request_rate_upper_limit
        cont.save()

    # PES normalization process
    if (total_pes > MAX_TOTAL_CONT_PES):
        for container in containers:
            cont = Container.objects.get(cont_id=container.id[:12])
            cont.next_pes = cont.next_pes * MAX_TOTAL_CONT_PES / total_pes
            cont.save()

    # Perform actual scaling
    for container in containers:
        cont = Container.objects.get(cont_id=container.id[:12])
        # Get container/app port
        port = subprocess.check_output(["docker port {0} | cut -d ':' -f 2".format(container.id)], shell=True)[:-1]
        # Scale PES
        with open(os.devnull, 'wb') as devnull: # suppress output
            subprocess.check_call(["docker update --cpus=\"" + str(cont.next_pes*total_available_pes) + "\" " + str(container.id)], shell=True, stdout=devnull, stderr=subprocess.STDOUT)
        # Define upper request rate upper limit
        post_url = "http://localhost:{0}/ca_tf/serverInfo/".format(port)
        data_json = {'number': cont.next_real_rr*INTERVAL}
        #r = requests.post(post_url, json=data_json)
        #print(r.text)