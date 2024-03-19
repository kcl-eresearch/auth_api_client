#!/usr/bin/python3

import requests
import socket
import sys
import yaml
from auth_api_client import config
from auth_api_client.common import log_error, log_info

try:
    with open("/etc/auth_api/maint_auth.yaml") as fh:
        maint_config = yaml.safe_load(fh)
except Exception as e:
    log_error(f"Failed loading config: {e}")
    sys.exit(1)

fqdn = socket.getfqdn()
url = f"https://{fqdn}/api/v{config.API_VERSION}/maint/notify_vpn_expiry"

try:
    r = requests.post(url, auth=(maint_config["username"], maint_config["password"]))
except Exception as e:
    log_error(f"Failed during POST request: {e}")
    sys.exit(1)

if r.status_code != 200:
    log_error(f"Unexpected status code from POST: {r.status_code}")
    log_error("Response was:")
    log_error(r.text)
    sys.exit(1)

try:
    response = r.json()
except Exception as e:
    log_error(f"Failed decoding response: {e}")
    log_error("Response was:")
    log_error(r.text)
    sys.exit(1)

if response["status"] == "ERROR":
    log_error(f"Error status from API, detail: {response['detail']}")
    sys.exit(1)

log_info(f"OK, {response['email_count']} emails sent")
