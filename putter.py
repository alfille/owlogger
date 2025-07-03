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
import owpy3


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
    except:
        print( datetime.datetime.now(), data_string ) 

def main(sysargs):
    # Command line first
    parser = argparse.ArgumentParser(
        prog="1-wire Logger",
        description="Log 1-wire data externally to protect interior sensors. Transmittter component",
        epilog="By Paul H Alfille 2025 -- repository: https://github.com/alfille/logger")

    # token list
    parser.add_argument('-t','--token',
        required=False,
        default=argparse.SUPPRESS,
        dest="token",
        type=str,
        nargs='*',
        help='Token to senfd with data (optonal arbitrary text string)'
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
        
    # One-wire owserver address
    default_owport = 4304
    owserver = f"localhost:{default_owport}"
    parser.add_argument('-o','--owserver',
        required=False,
        default=owserver,
        dest="owserver",
        nargs='?',
        help=f'owserver network address (optional) default={owserver}'
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
        
        
    args=parser.parse_args()
    print(sysargs,args)

    #token
    if "token" in args:
        token = args.token
    else:
        token = None

    #server
    server = args.server

    #owserver
    if args.owserver.find("//")==-1:
        owserver = args.owserver
    else:
        owserver = args.owserver.split("//")[1]
    if owserver.find(":")==-1:
        owserver_port = default_owport
    else:
        (owserver, owserver_port) = owserver.split(":")

    #period
    if "period" in args:
        period = args.period
        if math.isnan(period):
            period = 30
    else:
        period = None

    # Loop
    while True:
        # owserver_connect( owserver, owserver_port )
        # Tdevices = devs_with_temerature()
        # Hdevices = devs_with_humidity()
        data_string = " ".join([
            " ".join(["T "+Temperature_read(d) for d in Tdevices]),
            " ".join(["H "+Humidity_read(d) for d in Hdevices])
        ])
        upload( server, token, owserver_data )

        if period==Null:
            # single shot
            break

        # delay and repeat
        time.sleep( 60*period )
        

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
