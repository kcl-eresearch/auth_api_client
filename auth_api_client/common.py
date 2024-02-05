import datetime
import json
import os
import requests
import sys
import syslog
import time
import yaml
from auth_api_client import config

def load_config():
    try:
        with open("/etc/auth_api_client.yaml") as fh:
            config.config = yaml.safe_load(fh)
    except Exception as e:
        sys.exit(f"Failed loading config: {e}")

    return config

def log_error(message):
    sys.stderr.write(f"{message}\n")

def log_info(message):
    syslog.syslog(syslog.LOG_INFO | syslog.LOG_AUTHPRIV, message)

def get_ssh_keys(username, remote_ip=None, ppid=None):
    if remote_ip and ppid:
        url = f"https://{config.config['host']}/api/v{config.API_VERSION}/ssh_auth/{username}/{remote_ip}"
        timeout = time.time() + config.config["timeout"]
        log_info("Processing auth request: %s" % json.dumps({"username": username, "remote_ip": remote_ip, "pid": os.getpid(), "ppid": ppid}))
        while time.time() < timeout:
            try:
                r = requests.get(url, auth=(config.config["username"], config.config["password"]))
                if r.status_code == 200:
                    try:
                        response = r.json()
                        if response["status"] == "OK":
                            if response["result"] == "ACCEPT":
                                log_info(f"Accepting authentication for {username} from {remote_ip}: {len(response['keys'])} keys")
                                return response["keys"]

                            if response["result"] == "REJECT":
                                log_info(f"Rejecting authentication for {username} from {remote_ip}: {response['reason']}")
                                return []

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

        log_info(f"Rejecting authentication for {username} from {remote_ip}: timeout")
        return []
    else:
        url = f"https://{config.config['host']}/api/v{config.API_VERSION}/ssh_keys/{username}"
        try:
            r = requests.get(url, auth=(config.config["username"], config.config["password"]))
            if r.status_code == 200:
                try:
                    response = r.json()
                    if response["status"] == "OK":
                        return response["keys"]

                    log_error(f"Unexpected status from {url}: {response['status']}")
                    return []
                except Exception as e:
                    log_error(f"Failed decoding response from {url}: {e}")
                    log_error("Response was:")
                    log_error(r.text)
            else:
                log_error(f"Unexpected HTTP status fetching {url}: {r.status_code}")
                return []
        except Exception as e:
            log_error(f"Failed fetching {url}: {e}")
            return []

def heading(string):
    print("%s\n%s" % (string, "=" * len(string)))

def format_ts(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
