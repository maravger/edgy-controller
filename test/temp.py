#!/usr/bin/env python
import docker
import os
import subprocess
import sys
from subprocess import call

# Get docker client 
client = docker.from_env()

# Get container Object
contsList = client.containers.list()
print contsList
cont = contsList[0]

# Update container resources
print cont.id
cont_id = cont.id
memoryUpdate = 2000
memoryUpdate = str(memoryUpdate)
os.system("docker update -m " + memoryUpdate + "MB " + cont_id) 

# Toggle between denying/accepting requests in container ports
subprocess.call(['sudo', sys.executable, './ufw_cust.py', 'deny', '8000'])
