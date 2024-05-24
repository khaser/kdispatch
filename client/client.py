#!/usr/bin/env python3
import argparse
import threading
import select
import socket
import daemon
from sys import argv

import requests
import paramiko


HOST_IP = '130.193.38.230'
REST_URL = f'http://{HOST_IP}:8080/api'

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

def spawn_tunnel(host_ip, local_port, remote_port):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
    client.connect(host_ip, 22, "anon", password="")

    transport = client.get_transport()
    transport.request_port_forward("", remote_port)
    while True:
        chan = transport.accept(1000)
        if chan is None:
            continue
        print("Connect request registred")
        thr = threading.Thread(
            target=resend_routine, args=(chan, "127.0.0.1", local_port)
        )
        thr.daemon = True
        thr.start()


def resend_routine(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        print("Forwarding request to %s:%d failed: %r" % (host, port, e))
        return

    print("Connected!  Tunnel open {} -> {} -> {}".format(chan.origin_addr, chan.getpeername(), (host, port)))

    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()
    print("Tunnel closed from %r" % (chan.origin_addr,))


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
        if not args.token:
            print("Specify you admin token to be able manage projects")
            exit (1)
        if not args.port:
            print("For `--start-hosting` you must specify `--port` for sharing")
            exit (1)
        r = requests.post(f'{REST_URL}/service/hosts', json={'service_token': args.token})
        if r.status_code == 200:
            remote_port, host_token = r.json().values()
            print_with_hint(host_token, "Above you can see you host token, which you should use to deactivite your hosting")
            print(f"DEBUG: local_port {args.port}, remote_port {remote_port}")
            with daemon.DaemonContext():
                spawn_tunnel(HOST_IP, int(args.port), int(remote_port))
            exit(0)
        elif r.status_code == 409:
            print(f"User with handle `{args.handle}` alredy exists. Please, try different handle")
            exit(1)
        else:
            print("Unrecognized server error")
            exit(2)
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
        elif r.status_code == 409:
            print(f"User with handle `{args.handle}` alredy exists. Please, try different handle")
            exit(1)
        else:
            print("Unrecognized server error")
            exit(2)
    elif args.proj_name:
        if not args.token:
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
        elif r.status_code == 409:
            print(f"Your project `{args.proj_name}` alredy exists. Please, pick different name, or remove project with `--delete-project`")
            exit(1)
        else:
            print("Unrecognized server error")
            exit(2)
    elif args.delete_project:
        pass



if __name__ == "__main__":
    main()
