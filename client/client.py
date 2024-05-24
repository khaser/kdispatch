#!/usr/bin/env python3
import argparse
import requests
from sys import argv

REST_URL = 'http://130.193.38.230:8080/api'

parser = argparse.ArgumentParser(prog="kdispatch")
# mode_group = parser.add_mutually_exclusive_group(required=True)
# mode_group.add_argument('--client', action='store_const', const='client')
# mode_group.add_argument('--host', action='store_const', const='host')

# parser.add_argument('--role', choices=['client', 'host', 'admin'], required=True)

parser.add_argument('--token', '-t', help="access token")
parser.add_argument('--port', '-p', help="local port for project sharing (if you are host) or receiving (if you are client)")

action_group = parser.add_mutually_exclusive_group()

# user
action_group.add_argument('--connect',  '-c', action='store_true', help="connect local port `port` to project")
action_group.add_argument('--disconnect', '-d', action='store_true', help="stop project sharing")

# hoster
action_group.add_argument('--start-hosting', action='store_true', help="start share project hosted on local `port`")
action_group.add_argument('--stop-hosting', action='store_true', help="stop project sharing")

# admin
action_group.add_argument('--sign-up', '-s', dest='handle', help="sign-up as administrator to get token allows project operations")

action_group.add_argument('--register-project', '-r', action='store_true', help="register new service")
action_group.add_argument('--delete-project', action='store_true', help="remove service")

# host_group = parser.add_argument_group('Hoster options')
# client_group = parser.add_argument_group('Client options')

def main():
    args = parser.parse_args(argv[1:])

    if args.connect:
        pass
    elif args.disconnect:
        pass
    elif args.start_hosting:
        pass
    elif args.stop_hosting:
        pass
    elif args.sign_up:
        r = requests.get(f'{REST_URL}/admin/register', params={'handle', args.handle})
        print(r.text)
    elif args.register_project:
        pass
    elif args.delete_project:
        pass



if __name__ == "__main__":
    main()
