#!/usr/bin/env python
from django.core.exceptions import ObjectDoesNotExist
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "controller.settings")
import django
django.setup()
import docker
from api.models import Container
import logging
import os
import requests
import subprocess
import sys
from subprocess import call

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

def scale():
    total_pes = 0
    total_available_pes = int(subprocess.check_output("docker -D info | grep CPUs | sed 's/^CPUs: //'", shell=True))

    # Get docker client
    client = docker.from_env()

    # Get containers
    containers = client.containers.list()

    # Calculate new operating conditions
    for container in containers:
        try:
            cont = Container.objects.get(cont_id=container.id)
        except ObjectDoesNotExist:
            # Create container representation in the db if it does not exist
            cont = Container(cont_id=container.id)
            cont.save()
        # logger.info('Container: ' + cont.cont_id)
        print('Container ID: ' + cont.cont_id)
        print('Container Host: ' + str(cont.host_id))
        print('Container Operating Point: ' + str(cont.op_point))
        print('Container Previous Response Time: ' + str(cont.prev_art))

        x0 = cont.prev_art
        op = cont.op_point
        app_id = cont.app_id
        pes_to_scale = K1[app_id][op] * (x0 - X_ART_REF[app_id][op]) + U_PES_REF[app_id][op]
        if pes_to_scale > U_PES_MAX[app_id][op]:
            pes_to_scale = U_PES_MAX[app_id][op]
        elif pes_to_scale < U_PES_MIN[app_id][op]:
            pes_to_scale = U_PES_MIN[app_id][op]
        print ('PES to allocate to Container: ' + str(pes_to_scale))
        cont.next_pes = pes_to_scale

        total_pes += pes_to_scale
        print ('Total allocated PES of this Host: ' + str(pes_to_scale))

        request_rate_upper_limit = K2[app_id][op] * (x0 - X_ART_REF[app_id][op]) + U_REQ_REF[app_id][op]
        if request_rate_upper_limit > U_REQ_MAX[app_id][op]:
            request_rate_upper_limit = U_REQ_MAX[app_id][op]
        elif request_rate_upper_limit < U_REQ_MIN[app_id][op]:
            request_rate_upper_limit = U_REQ_MIN[app_id][op]
        print ('Request Rate Upper Limit for Container: ' + str(request_rate_upper_limit))
        cont.next_real_rr = request_rate_upper_limit
        cont.save()

    # PES normalization process
    if (total_pes > MAX_TOTAL_CONT_PES):
        for container in containers:
            cont = Container.objects.get(cont_id=container.id)
            cont.next_pes = cont.next_pes * MAX_TOTAL_CONT_PES / total_pes
            cont.save()

    # Perform actual scaling
    for container in containers:
        cont = Container.objects.get(cont_id=container.id)
        ip = subprocess.check_output(["docker", "inspect", "-f", "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'", container.id])
        # Scale PES
        os.system("docker update --cpus=\"" + str(cont.next_pes*total_available_pes) + "\" " + str(container.id))
        # Define upper rr upper limit
        post_url = "http://" + ip + "/ca_tf/serverInfo/"
        data_json = {'number': cont.next_real_rr*INTERVAL}
        #r = requests.post(post_url, json=data_json)
        #print(r.text)


    # print containers

    # cont = containers[0]

    # Update container resources
    # print cont.id
    # cont_id = cont.id
    # memoryUpdate = 100
    # memoryUpdate = str(memoryUpdate)
    # cpuUpdate = 2
    # cpuUpdate = str(cpuUpdate)
    # os.system("docker update -m " + memoryUpdate + "M --memory-swap " + 2*memoryUpdate + "M " + cont_id)
    # os.system("docker update --cpus=\"" + cpuUpdate + "\" " + cont_id)

# For debugging purposes
def main():
    scale()

if __name__ == "__main__":
    main()