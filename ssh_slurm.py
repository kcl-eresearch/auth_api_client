#!/usr/bin/python3
#
# Version of ssh.py which checks for active Slurm jobs

import pwd
import socket
import subprocess
import sys
from auth_api_client.common import get_ssh_keys, load_config, log_error, log_info

API_VERSION = 1
config = {}
load_config()

if len(sys.argv) < 2:
    log_error("No user specified")
    sys.exit(1)

try:
    user = pwd.getpwnam(sys.argv[1])
except Exception as e:
    log_error("Invalid user specified")
    sys.exit(1)

try:
    result = subprocess.run(["/usr/bin/squeue", "-t", "running", "-u", user.pw_name, "-w", socket.gethostname().split(".")[0], "-h", "-o", "%u"], capture_output=True, check=True)
except Exception as e:
    log_error(f"Failed getting user slurm jobs: {e}")
    sys.exit(1)

if len(result.stdout.decode().splitlines()) == 0:
    log_info(f"Denying authentication for {user.pw_name}: no jobs running here")
    sys.exit(1)

for key in get_ssh_keys(user.pw_name):
    print(f"{key['type']} {key['pub_key']}")

sys.stdout.flush()
