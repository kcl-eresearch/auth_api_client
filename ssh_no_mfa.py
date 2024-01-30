#!/usr/bin/python3
#
# Version of ssh.py which just returns all SSH keys for a user
# For use on "legacy" hosts without doing web MFA

import os
import json
import pwd
import sys
import yaml
from auth_api_client.common import get_ssh_keys, load_config, log_error

API_VERSION = 1
CMD_MAP = {
    "rsync": "/usr/bin/rrsync /",
    "rsync_ro": "/usr/bin/rrsync -ro /",
    "sftp": "internal-sftp",
    "sftp_ro": "internal-sftp -R"
}
CMD_BOGUS = "/usr/sbin/nologin"
SCRIPT_NAME = os.path.basename(sys.argv[0]).split(".")[0]

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

# Drop root privileges no longer required
pwentry = pwd.getpwnam(config["run_as"])
os.setgid(pwentry.pw_gid)
os.setgroups([])
os.setuid(pwentry.pw_uid)

for key in get_ssh_keys(user.pw_name):
    if SCRIPT_NAME == "ssh_tre_sftp" and key["access_type"] != "sftp":
        continue

    if SCRIPT_NAME == "ssh_ro_sftp" and key["access_type"] != "sftp_ro":
        continue

    restrictions = []
    if key["allowed_ips"]:
        try:
            allowed_ips = ",".join(json.loads(key["allowed_ips"]))
        except: # Play it safe and don't allow key if invalid allowed_ips
            continue
        restrictions.append("from=\"%s\"" % allowed_ips)
    else:
        if SCRIPT_NAME == "ssh_tre_sftp":
            continue

    command = None
    if key["access_type"] != "any":
        restrictions.append("restrict")

        if key["access_type"] in CMD_MAP:
            command = CMD_MAP[key["access_type"]]
        else:
            command = CMD_BOGUS

        restrictions.append("command=\"%s\"" % command)

    print((" ".join([",".join(restrictions), key["type"], key["pub_key"]])).strip())

sys.stdout.flush()
