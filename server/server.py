#!/usr/bin/env python3
import argparse
from sys import argv

parser = argparse.ArgumentParser(prog="kserver-dispatch")
parser.add_argument('--db_ip', nargs=1, required=True)

def main():
    args = parser.parse_args(argv[1:])

    try
        db_ip = args.db_ip[0]
    except:
        print("Db ip is undefined")
        return 0

    print("Using database ip is:", args.db_ip)

if __name__ == "__main__":
    main()
