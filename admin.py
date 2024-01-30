#!/usr/bin/python3

import argparse
import sys
import tabulate
from auth_api_client.common import api_get, format_ts, heading, load_config, validate_user

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", type=validate_user)
parser.add_argument("-m", "--mfa", action="store_true")
args = parser.parse_args()

if args.user and args.mfa:
    sys.stderr.write("Cannot combine --user and --mfa options\n")
    sys.exit(1)

if not (args.user or args.mfa):
    sys.stderr.write("Please specify either --mfa or --user USER\n")
    sys.exit(1)

API_VERSION = 1
config = {}
load_config()

if args.user:
    heading(f"SSH keys for {args.user}")
    ssh_keys = api_get(f"ssh_keys/{args.user}")
    for key in ssh_keys["keys"]:
        print()
        print(f"Name: {key['name']}")
        print(f"Created: {format_ts(key['created_at'])}")
        print(f"Key: {key['type']} {key['pub_key']}")
    
    print()
    
    heading(f"VPN certificates for {args.user}")
    vpn_keys = api_get(f"vpn_keys/{args.user}")
    for key in vpn_keys["keys"]:
        print()
        print(f"Name: {key['name']}")
        print(f"UUID: {key['uuid']}")
        print(f"Status: {key['status']}")
        print(f"Created: {format_ts(key['created_at'])}")
        print(f"Expires: {format_ts(key['expires_at'])}")
        print("Public certificate:")
        print(key["public_cert"])
    
    print()

    heading(f"MFA requests for {args.user}")    
    mfa_requests = api_get(f"mfa_requests/{args.user}")
    to_print = []
    for mfa in mfa_requests["mfa_requests"]:
        row = {}
        row["Created"] = format_ts(key['created_at'])
        row["Updated"] = format_ts(key['updated_at'])
        if mfa["expires_at"]:
            row["Expires"] = format_ts(key['expires_at'])
        else:
            row["Expires"] = "n/a"
        row["Service"] = mfa["service"]
        row["IP address"] = mfa["remote_ip"]
        row["Status"] = mfa["status"]
        to_print.append(row)
    
    print(tabulate.tabulate(to_print, headers="keys"))

if args.mfa:
    heading("MFA requests for all users")
    mfa_requests = api_get("mfa_requests")
    to_print = []
    for mfa in mfa_requests["mfa_requests"]:
        row = {}
        row["Username"] = mfa["username"]
        row["Created"] = format_ts(key['created_at'])
        row["Updated"] = format_ts(key['updated_at'])
        if mfa["expires_at"]:
            row["Expires"] = format_ts(key['expires_at'])
        else:
            row["Expires"] = "n/a"
        row["Service"] = mfa["service"]
        row["IP address"] = mfa["remote_ip"]
        row["Status"] = mfa["status"]
        to_print.append(row)
    
    print(tabulate.tabulate(to_print, headers="keys"))
