#!/usr/bin/env python3
# generalpost.py
#
# owlogger upload data
#
# Paul H Alfille 2025
# MIT license

# Example from https://pytutorial.com/python-requestsput-complete-guide-for-http-put-requests/

from requests import put as send_put
import json
import datetime
import argparse
import sys
import math
import time
from pyownet import protocol

# for authentification
try:
    import jwt
    has_jwt = True
except:
    has_jet = False


def upload( server, secret, data_string ):
    data = json.dumps( {'data': data_string } )
    if secret==None:
        post( server, data, { "Content-Type": "application/text"} )
    else:
        post( server, data, { 'Authorization': f'Bearer {secret}', 'Content-Type': 'application/text'} )

def post( server, data, headers ): 
    try:
        response = send_post( server, data, headers )
        global debug
        if debug:
            print( f"Return code={response.status_code} ({response.reason}) from {response.url}")
    except:
        print( datetime.datetime.now(), data ) 

def main(sysargs):
    # Command line first
    parser = argparse.ArgumentParser(
        prog="generalpost",
        description="Log any data to owlogger. Transmittter component",
        epilog="By Paul H Alfille 2025 -- repository: https://github.com/alfille/owlogger")

    # text to send
    parser.add_argument("message",
        nargs="+",
        help="Text message to send to owlogger"
        )

    # Server address
    default_port = 8001
    server = f"localhost:{default_port}"
    parser.add_argument('-s','--server',
        required=False,
        default=server,
        dest="server",
        nargs='?',
        help=f'Server network address (optional) default={server}\t\nNote that this default is a local testing setup.'
        )
        
    # name
    parser.add_argument('-n','--name',
        required=False,
        default="generalpost",
        dest="name",
        nargs='?',
        type=str,
        help=f'Optional name for data source. Default owpost'
        )
        
    # token
    parser.add_argument('-t','--token',
        required=False,
        default=argparse.SUPPRESS,
        dest="token",
        type=str,
        nargs='?',
        help='Secret token to authentificate message (optonal arbitrary text string)'
        )

    # debug output
    parser.add_argument('-d', '--debug', 
        required=False,
        action='store_true',
        dest="debug",
        help='debug output'
        )
        
        
    args=parser.parse_args()
    print(sysargs,args)

    #JWT token
    if "token" in args:
        if has_jwt:
            secret = jwt.encode( {'name':args.name},args.token,algorithm='HS256')
        else:
            print("Error: token for JWT authentification supplied, but pyJWT not installed")
            print("Suggest apt install python3-jwt")
            sys.exit(2)
    else:
        secret=None

    #server
    server = args.server

    # debug
    global debug
    debug = args.debug
    if debug:
        print("Debugging on")

    upload( server, secret, " ".join(args.message) )

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
