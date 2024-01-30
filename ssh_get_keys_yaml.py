#!/usr/bin/python3
#
# Get specified user's keys and return in yaml format

import os
import pwd
import sys
import yaml
from auth_api_client.common import get_ssh_keys, load_config, log_error

API_VERSION = 1
config = {}
load_config()

if len(sys.argv) < 2:
    log_error("No user specified")
    sys.exit(1)

# Drop root privileges no longer required
pwentry = pwd.getpwnam(config["run_as"])
os.setgid(pwentry.pw_gid)
os.setgroups([])
os.setuid(pwentry.pw_uid)

keys = []
for key in get_ssh_keys(sys.argv[1]):
    keys.append(key)

print(yaml.dump(keys))
sys.stdout.flush()
