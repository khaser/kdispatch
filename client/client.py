#!/usr/bin/env python3
import argparse
import select
import socket
import socketserver
import random
import threading
import tempfile

from sys import argv

import daemon
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
parser.add_argument('--port', '-p', type=int, help="local port for project sharing (if you are host) or receiving (if you are client)")
parser.add_argument('--detach', action='store_true', help="detach application from console after `--start-hosting`")
parser.add_argument('--service', '-s', metavar="handle/service-name", help="specify service for `--connect` and `--list` actions")

action_group = parser.add_mutually_exclusive_group(required=True)

# user
action_group.add_argument('--connect',  '-c', action='store_true', help="connect local port `port` to project")
action_group.add_argument('--list', '-l', action='store_true', help="show available hosts for specified project")

# hoster
action_group.add_argument('--start-hosting', action='store_true', help="start share project hosted on local `port`")

# admin
action_group.add_argument('--sign-up', dest='handle', help="sign-up as administrator to get token allows project operations")

action_group.add_argument('--register-project', '-r', dest='proj_name', help="register new service with `proj-name`")
# action_group.add_argument('--delete-project', action='store_true', help="remove service")

def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
    client.connect(HOST_IP, 22, "anon", password="")
    return client.get_transport()


def remote_tunnel(local_port, remote_port, host_token):
    transport = ssh_connect()
    transport.request_port_forward("", remote_port)
    while True:
        chan = transport.accept(1000)
        if chan is None:
            continue
        print("Connect request registred")
        sock = try_connect("127.0.0.1", local_port)
        if sock is None:
            deregister_hosting(host_token)
            return
        thr = threading.Thread(
            target=resend_routine, args=(chan, sock)
        )
        thr.daemon = True
        thr.start()


def resend_routine(chan, sock, checkOnly=False):
    # print("Connected!  Tunnel open {} -> {} -> {}".format(chan.origin_addr, chan.getpeername(), (host, port)))

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
    print("Tunnel closed")


def local_tunnel(local_port, remote_port):

    class ForwardServer(socketserver.ThreadingTCPServer):
        # daemon_threads = True
        allow_reuse_address = True

        def handle_error(self, request, client_addr):
            self.shutdown()

    class ForwardHandler(socketserver.BaseRequestHandler):
        def handle(self):
            chan = ssh_connect().open_channel("direct-tcpip", (HOST_IP, remote_port), self.request.getpeername())
            resend_routine(self.request, chan)

    ForwardServer(("", local_port), ForwardHandler).serve_forever()


def try_connect(host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        print("Connecting to %s:%d failed: %r" % (host, port, e))
        return None
    return sock


def deregister_hosting(host_token):
    r = requests.delete(f'{REST_URL}/service/hosts', json={'host_token': host_token})
    if r.status_code == 200:
        print("Host successfully deregistered")
    elif r.status_code == 403:
        print("Incorrect host token, client-server protocol BUG!")
    else:
        print("Internal server error")


def get_hosters(service):
    handle, name = service.split('/')
    r = requests.get(f'{REST_URL}/service/hosts', params={'handle': handle, 'name' : name})
    if r.status_code != 200:
        print("Unrecognized server error")
        exit(2)
    return r.json()


def main():
    args = parser.parse_args(argv[1:])

    def print_with_hint(token, hint):
        if args.quiet:
            print(token)
        else:
            print(token)
            print(hint)

    try:
        if args.list:
            if not args.service:
                print("Specify service via `--service` argument")
                exit (1)
            print("List of available remote ports on which service provided:\n", *get_hosters(args.service), sep='\n\t')
        elif args.connect:
            if not args.service:
                print("Specify service via `--service` argument")
                exit (1)
            if not args.port:
                print("Specify local port via `--port` argument")
                exit (1)
            service_ports = get_hosters(args.service)
            if len(service_ports) == 0:
                print("No hosts which provide requested service")
                exit (1)
            remote_port = int(random.choice(service_ports))
            print(remote_port)
            if args.detach:
                with daemon.DaemonContext():
                    local_tunnel(args.port, remote_port)
            else:
                local_tunnel(args.port, remote_port)
        elif args.start_hosting:
            if not args.token:
                print("Specify you admin token to be able manage projects")
                exit (1)
            if not args.port:
                print("For `--start-hosting` you must specify `--port` for sharing")
                exit (1)
            r = requests.post(f'{REST_URL}/service/hosts', json={'service_token': args.token})
            if r.status_code == 409:
                print(f"User with handle `{args.handle}` alredy exists. Please, try different handle")
                exit(1)
            elif r.status_code != 200:
                print("Unrecognized server error")
                exit(2)
            remote_port, host_token = r.json().values()
            remote_port = int(remote_port)

            sock = try_connect("127.0.0.1", args.port)
            if not sock:
                print(f"Failed to connect to local port, check that you provide application on port {args.port}")
                deregister_hosting(host_token)
                exit(1)
            else:
                sock.close()

            print("Hosting will be stopped automatically when specified service port is closed")

            print(f"DEBUG: host_token {host_token}, local_port {args.port}, remote_port {remote_port}")
            if args.detach:
                with daemon.DaemonContext():
                    remote_tunnel(args.port, remote_port, host_token)
            else:
                remote_tunnel(args.port, remote_port, host_token)
            exit(0)
        elif args.handle:
            r = requests.get(f'{REST_URL}/admin/register', params={'handle': args.handle})
            if r.status_code == 409:
                print(f"User with handle `{args.handle}` alredy exists. Please, try different handle")
                exit(1)
            elif r.status_code != 200:
                print("Unrecognized server error")
                exit(2)
            print_with_hint(r.text,
                            "Above you can see you administrator token. Save it and specify\n"
                            "for project-managing operations (e.g. --register-project) using --token argument"
                            )
            exit(0)
        elif args.proj_name:
            if not args.token:
                print("Specify you admin token to be able manage projects")
                exit (1)
            r = requests.post(f'{REST_URL}/service/register', json={'admin_token': args.token, 'name': args.proj_name})
            if r.status_code == 403:
                print("Incorrect credentials")
                exit(1)
            elif r.status_code == 409:
                print(f"Your project `{args.proj_name}` alredy exists. Please, pick different name, or remove project with `--delete-project`")
                exit(1)
            elif r.status_code != 200:
                print("Unrecognized server error")
                exit(2)
            print_with_hint(r.text,
                            "Above you can see service hoster token. Save it and share with peoples, who\n"
                            "should be able to host your service with `--start-hosting`. \n"
                            "Of course, you can use that token by yourself"
                            )
            exit(0)
        # elif args.delete_project:
        #     pass
    except ConnectionRefusedError as e:
        print("Failed connect to kdispatch proxy server: {HOST_IP}")


if __name__ == "__main__":
    main()
