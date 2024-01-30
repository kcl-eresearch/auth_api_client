#!/usr/bin/python3
#
# Version of ssh.py which is for service accounts
# These don't use MFA but are IP address restricted

import os
import pwd
import sys
from auth_api_client import config
from auth_api_client.common import get_ssh_keys, load_config, log_error

load_config()

if len(sys.argv) < 2:
    log_error("No user specified")
    sys.exit(1)

try:
    user = pwd.getpwnam(sys.argv[1])
except Exception as e:
    log_error("Invalid user specified")
    sys.exit(1)

if "service_account_restrict_users" in config.config and user.pw_name in config.config["service_account_restrict_users"]:
    ip_allowed = config.config["service_account_restrict_users"][user.pw_name]
elif "service_account_restrict" in config.config:
    ip_allowed = config.config["service_account_restrict"]
else:
    ip_allowed = ["127.0.0.0/8"]

ip_allowed_csv = ",".join(ip_allowed)

# Drop root privileges no longer required
pwentry = pwd.getpwnam(config.config["run_as"])
os.setgid(pwentry.pw_gid)
os.setgroups([])
os.setuid(pwentry.pw_uid)

for key in get_ssh_keys(user.pw_name):
    print(f"from=\"{ip_allowed_csv}\" {key['type']} {key['pub_key']}")

sys.stdout.flush()
