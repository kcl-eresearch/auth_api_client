#!/usr/bin/python3

import json
import os
import pwd
import psutil
import sys
from auth_api_client.common import get_ssh_keys, load_config, log_error, log_info

API_VERSION = 1
CMD_RSYNC = "/usr/bin/rrsync /"
CMD_SFTP="internal-sftp"
CMD_BOGUS="/usr/sbin/nologin"

config = {}
load_config

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
pwentry = pwd.getpwnam(config["run_as"])
os.setgid(pwentry.pw_gid)
os.setgroups([])
os.setuid(pwentry.pw_uid)

for key in get_ssh_keys(user.pw_name, remote_ip):
    restrictions = []
    if key["allowed_ips"]:
        try:
            allowed_ips = ",".join(json.loads(key["allowed_ips"]))
        except: # Play it safe and don't allow key if invalid allowed_ips
            continue
        restrictions.append("from=\"%s\"" % allowed_ips)

    if key["access_type"] != "any":
        restrictions.append("restrict")

        if key["access_type"] == "rsync":
            command = CMD_RSYNC
        elif key["access_type"] == "sftp":
            command = CMD_SFTP
        else:
            command = CMD_BOGUS

        restrictions.append("command=\"%s\"" % command)

    print((" ".join([",".join(restrictions), key["type"], key["pub_key"]])).strip())

sys.stdout.flush()
