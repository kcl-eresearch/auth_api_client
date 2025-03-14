#!/usr/bin/python3
#
# Get specified user's keys and return in yaml format

import os
import pwd
import sys
import yaml
from auth_api_client import config
from auth_api_client.common import get_ssh_keys, load_config, log_error

load_config()

if len(sys.argv) < 2:
    log_error("No user specified")
    sys.exit(1)

keys = []
for key in get_ssh_keys(sys.argv[1]):
    keys.append(key)

print(yaml.dump(keys))
sys.stdout.flush()
