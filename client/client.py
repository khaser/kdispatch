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
parser.add_argument('--quiet', '-q', action='store_true', help="prevent hints, may be usable for scripting")
parser.add_argument('--port', '-p', help="local port for project sharing (if you are host) or receiving (if you are client)")

action_group = parser.add_mutually_exclusive_group(required=True)

# user
action_group.add_argument('--connect',  '-c', action='store_true', help="connect local port `port` to project")
action_group.add_argument('--disconnect', '-d', action='store_true', help="stop project sharing")

# hoster
action_group.add_argument('--start-hosting', action='store_true', help="start share project hosted on local `port`")
action_group.add_argument('--stop-hosting', action='store_true', help="stop project sharing")

# admin
action_group.add_argument('--sign-up', '-s', dest='handle', help="sign-up as administrator to get token allows project operations")

action_group.add_argument('--register-project', '-r', dest='proj_name', help="register new service with `proj-name`")
action_group.add_argument('--delete-project', action='store_true', help="remove service")

# host_group = parser.add_argument_group('Hoster options')
# client_group = parser.add_argument_group('Client options')


def main():
    args = parser.parse_args(argv[1:])

    def print_with_hint(token, hint):
        if args.quiet:
            print(token)
        else:
            print(token)
            print(hint)

    print(args)

    if args.connect:
        pass
    elif args.disconnect:
        pass
    elif args.start_hosting:
        pass
    elif args.stop_hosting:
        pass
    elif args.handle:
        r = requests.get(f'{REST_URL}/admin/register', params={'handle': args.handle})
        if r.status_code == 200:
            print_with_hint(r.text,
                            "Above you can see you administrator token. Save it and specify\n"
                            "for project-managing operations (e.g. --register-project) using --token argument"
                            )
            exit(0)
        elif r.status_code == 406:
            print(f"User with handle `{args.handle}` alredy exists. Please, try different handle")
            exit(1)
        else:
            print("Unrecognized server error")
            exit(2)
    elif args.proj_name:
        if 'token' not in args:
            print("Specify you admin token to be able manage projects")
            exit (1)
        r = requests.post(f'{REST_URL}/service/register', json={'admin_token': args.token, 'name': args.proj_name})
        if r.status_code == 200:
            print_with_hint(r.text,
                            "Above you can see service hoster token. Save it and share with peoples, who\n"
                            "should be able to host your service with `--start-hosting`. \n"
                            "Of course, you can use that token by yourself"
                            )
            exit(0)
        elif r.status_code == 403:
            print("Incorrect credentials")
            exit(1)
        elif r.status_code == 406:
            print(f"Your project `{args.proj_name}` alredy exists. Please, pick different name, or remove project with `--delete-project`")
            exit(1)
        else:
            print("Unrecognized server error")
            exit(2)
    elif args.delete_project:
        pass



if __name__ == "__main__":
    main()
