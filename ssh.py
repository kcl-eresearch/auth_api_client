#!/usr/bin/python3

import json
import os
import pwd
import psutil
import sys
from auth_api_client import config
from auth_api_client.common import get_ssh_keys, load_config, log_error, get_ssh_key_extra_options

CMD_MAP = {
    "rsync": "/usr/bin/rrsync",
    "rsync_ro": "/usr/bin/rrsync -ro",
    "rsync_wo": "/usr/bin/rrsync -wo",
    "sftp": "internal-sftp",
    "sftp_ro": "internal-sftp -R"
}
CMD_BOGUS = "/usr/sbin/nologin"

load_config()

ppid = os.getppid()
p_sshd = psutil.Process(ppid)
if p_sshd.exe() != "/usr/sbin/sshd":
    log_error("Parent process is not sshd")
    sys.exit(1)

if len(sys.argv) < 2:
    log_error("No user specified")
    sys.exit(1)

try:
    user = pwd.getpwnam(sys.argv[1])
except Exception as e:
    log_error("Invalid user specified")
    sys.exit(1)

remote_ip = None
for conn in psutil.net_connections(kind="tcp"):
    if conn.laddr[1] == 22 and conn.status == psutil.CONN_ESTABLISHED:
        proc = psutil.Process(conn.pid)
        if proc.ppid() == ppid and proc.username() == "sshd":
            remote_ip = conn.raddr[0]
            break

if not remote_ip:
    log_error("Cannot determine remote IP address")
    sys.exit(1)

# Drop root privileges no longer required
pwentry = pwd.getpwnam(config.config["run_as"])
os.setgid(pwentry.pw_gid)
os.setgroups([])
os.setuid(pwentry.pw_uid)

for key in get_ssh_keys(user.pw_name, remote_ip, ppid):
    restrictions = []
    if key["allowed_ips"]:
        try:
            allowed_ips = ",".join(json.loads(key["allowed_ips"]))
        except: # Play it safe and don't allow key if invalid allowed_ips
            continue
        restrictions.append("from=\"%s\"" % allowed_ips)

    if key["access_type"] != "any":
        restrictions.append("restrict")

        if key["access_type"] in CMD_MAP:
            command = CMD_MAP[key["access_type"]]
        else:
            command = CMD_BOGUS

        if key["access_type"].startswith("rsync"):
            extra_options = get_ssh_key_extra_options(key)
            if "rsync_directory" in extra_options:
                command += " %s" % extra_options["rsync_directory"]
            else:
                command += " /"

        restrictions.append("command=\"%s\"" % command)

    print((" ".join([",".join(restrictions), key["type"], key["pub_key"]])).strip())

sys.stdout.flush()
