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
from pyownet import protocol


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
        
    # Celsius
    parser.add_argument( "-C", "--Celsius",
        required=False,
        default=protocol.FLG_TEMP_F,
        const=protocol.FLG_TEMP_C,
        dest="temp_scale",
        action = "store_const",
        help="Use Celsius temperature scale for readings. Default: Fahrenheit"
        )

    # Fahrenheit
    parser.add_argument( "-F", "--Fahrenheit",
        required=False,
        default=protocol.FLG_TEMP_F,
        const=protocol.FLG_TEMP_F,
        dest="temp_scale",
        action = "store_const",
        help="Use Fahrenheit temperature scale for readings. Default: Fahrenheit"
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



    #owserver
    if args.owserver.find("//")==-1:
        owserver = args.owserver
    else:
        owserver = args.owserver.split("//")[1]
    if owserver.find(":")==-1:
        owserver_host = owserver
        owserver_port = default_owport
    else:
        (owserver_host, owserver_port) = owserver.split(":")

    #
    # create owserver proxy object
    #
    try:
        owproxy = protocol.proxy(
            owserver_host, owserver_port, 
            flags=args.temp_scale,
            verbose=args.debug, )
    except protocol.ConnError as error:
        print(f"Unable to open connection to '{owserver_host}:{owserver_port}'\nSystem error: {error}", file=sys.stderr)
        sys.exit(1)
    except protocol.ProtocolError as error:
        print("'{owserver_host}:{owserver_port}' not an owserver?\nProtocol error: {error}", file=sys.stderr)
        sys.exit(1)

    #period
    if "period" in args:
        period = args.period
        if math.isnan(period):
            period = 30
    else:
        period = None

    # Loop
    while True:
        # Get Temperatures
        no_data = True
        temperatures = []
        for sensor in owproxy.dir(slash=False, bus=False):
            #stype = owproxy.read(sensor + '/type').decode()
            try:
                temp = float(owproxy.read(sensor + '/temperature'))
                temperatures.append( temp )
            except protocol.OwnetError:
                pass
        if len(temperatures)>0:
            temperature_string = " ".join([f"T {t:.2f}" for t in temperatures])
            no_data = False
            
        # Hdevices = devs_with_humidity() -- future
        
        if no_data:
            upload( server, token, "no data" )
        else:
            upload( server, token, " ".join([temperature_string]) )

        if period==None:
            # single shot
            break

        # delay and repeat
        time.sleep( 60*period )
        

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
