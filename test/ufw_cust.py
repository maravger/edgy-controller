#!/usr/bin/env python

import os
import sys

print sys.argv[1]
os.system('ufw ' + sys.argv[1] + " " + sys.argv[2])
