#!/usr/bin/python3

import grp
import os
import pwd
import re
import requests
import sys
import time
import yaml
from auth_api_client import config
from auth_api_client.common import load_config, log_error, log_info

def auth_vpn_group(username):
    openvpn_groups = []
    try:
        with open("/etc/openvpn_groups.yaml") as fh:
            openvpn_groups = yaml.safe_load(fh)

    except Exception as e:
        log_error("Failed loading group list: %s" % e)
        return False

    user_group_ids = []
    try:
        user_group_ids = os.getgrouplist(username, pwd.getpwnam(username).pw_gid)
    except Exception as e:
        log_error("Failed getting group information for user %s: %e" % (username, e))
        return False

    for group_id in user_group_ids:
        if grp.getgrgid(group_id).gr_name in openvpn_groups:
            return True

    return False

def auth_vpn_mfa_bypass(cert_cn, remote_ip):
    try:
        with open("/etc/openvpn_mfa_bypass.yaml") as fh:
            bypass_addresses = yaml.safe_load(fh)
    except Exception:
        return False

    if bypass_addresses == None:
        return False

    if not remote_ip in bypass_addresses:
        return False

    for cn in bypass_addresses[remote_ip]:
        if cn == cert_cn:
            return True

    return False

def auth_vpn_access(cert_cn, remote_ip):
    url = f"https://{config.config['host']}/api/v{config.API_VERSION}/vpn_auth/{cert_cn}/{remote_ip}"
    timeout = time.time() + config.config["timeout"]

    if auth_vpn_mfa_bypass(cert_cn, remote_ip):
        log_info(f"Accepting authentication from {remote_ip} with certificate {cert_cn} - MFA bypass")
        return 0

    while time.time() < timeout:
        try:
            r = requests.get(url, auth=(config.config["username"], config.config["password"]))
            if r.status_code == 200:
                try:
                    response = r.json()
                    if response["status"] == "OK":
                        if response["result"] == "ACCEPT":
                            if auth_vpn_group(response['username']):
                                log_info(f"Accepting authentication for {response['username']} from {remote_ip} with certificate {cert_cn}")
                                return 0

                            else:
                                log_info(f"Rejecting authentication for {response['username']} from {remote_ip} with certificate {cert_cn}: not in access groups")
                                return 1

                        if response["result"] == "REJECT":
                            log_info(f"Rejecting authentication for {response['username']} from {remote_ip} with certificate {cert_cn}: {response['reason']}")
                            return 1

                        if response["result"] == "PENDING":
                            pass
                        else:
                            log_error(f"Unexpected result from {url}: {e}")
                except Exception as e:
                    log_error(f"Failed decoding response from {url}: {e}")
                    log_error("Response was:")
                    log_error(r.text)
            else:
                log_error(f"Unexpected HTTP status fetching {url}: {r.status_code}")
        except Exception as e:
            log_error(f"Failed fetching {url}: {e}")

        time.sleep(2)

    log_info(f"Rejecting authentication for {response['username']} from {remote_ip}: timeout")
    return 1

load_config()

pwentry = pwd.getpwnam(config.config["run_as"])
os.setgid(pwentry.pw_gid)
os.setgroups([])
os.setuid(pwentry.pw_uid)

if "common_name" not in os.environ:
    log_error("No common_name provided")
    sys.exit(1)

if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", os.environ["common_name"]):
    log_error(f"Invalid common_name {os.environ['common_name']}")
    sys.exit(1)

if "trusted_ip" not in os.environ:
    log_error("No trusted_ip provided")
    sys.exit(1)

if not re.match(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$", os.environ["trusted_ip"]):
    log_error("Invalid trusted_ip {os.environ['trusted_ip']}")
    sys.exit(1)

sys.exit(auth_vpn_access(os.environ["common_name"], os.environ["trusted_ip"]))
