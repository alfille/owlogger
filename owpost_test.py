#!/usr/bin/env python3
# putter.py
#
# owfs machine upload data
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


def upload( server, token, data_string ):
    if token==None:
        j = json.dumps( {'data': data_string } )
    else:
        j = json.dumps( {'token':token, 'data': data_string } )

    try:
        response = send_put(
            server,
            data = j ,
            headers = { "Content-Type": "application/text"}
            )
        global debug
        if debug:
            print( f"Return code={response.status_code} ({response.reason}) from {response.url}")
    except Exception as e:
        print( f"Error {e} {datetime.datetime.now()} sending {data_string}" ) 

def main(sysargs):
    # Command line first
    parser = argparse.ArgumentParser(
        prog="1-wire Logger",
        description="Log 1-wire data externally to protect interior sensors. Transmittter tester",
        epilog="By Paul H Alfille 2025 -- repository: https://github.com/alfille/logger")

    # token list
    parser.add_argument('-t','--token',
        required=False,
        default=argparse.SUPPRESS,
        dest="token",
        type=str,
        nargs='*',
        help='Token to send with data (optonal arbitrary text string)'
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
                
    # periodic
    parser.add_argument('-p','--period',
        required=False,
        default=argparse.SUPPRESS,
        dest="period",
        nargs='?',
        type=int,
        help=f'Period (minutes) to repeat reading and sending (single-shot if not present)'
        )
        
    # messages
    parser.add_argument('messages',
        nargs="*",
        default=["put_test message"],
        help="Arbitratry messages to send"
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

    #token
    if "token" in args:
        token = args.token
    else:
        token = None

    #server
    server = args.server

    # debug
    global debug
    debug = args.debug
    if debug:
        print("Debugging on")

    #period
    if "period" in args:
        period = args.period
        if math.isnan(period):
            period = 30
    else:
        period = None

    # Loop
    while True:
        for m in args.messages:
            upload( server, token, m )

        if period==None:
            # single shot
            break

        # delay and repeat
        time.sleep( 60*period )
        

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
