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

# for authentification
try:
    import jwt
except:
    print("JWT module needs to be installed")
    print("either 'pip install PyJWT' or 'apt install python3-jwt'")
    sys.exit(1)

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
    # Look for a config file location (else default) 
    # read it in TOML format
    # allow command line parameters to over-rule
    
    # Step 1: Parse only the --config argument
    parser = argparse.ArgumentParser(
        add_help=False
        )
    
    config = "/etc/owlogger/owpost.toml"
    # config
    parser.add_argument("--config",
        required=False,
        default=config,
        dest="config",
        type=str,
        nargs="?",
        help=f"Location of any configuration file. Optional default={config}"
        )
    args, remaining_argv = parser.parse_known_args()

    # Process TOML
    # TOML file
    if "config" in args:
        try:
            with open( initial_args.config, "rb" ) as c:
                contents = c.readlines()
                try:
                    toml=tomllib.loads(contents)
                except TOMLDecodeError as e:
                    for lin in zip(range(1,200),contents.split("\n")):
                        print(f"{lin[0]:3d}. {lin[1]}")
                    print(f"Trouble reading configuration file {args.config}: {e.msg}")
                    sys.exit(1)
        except Exception as e:
            print(f"Cannot open TOML configuration file: {args.config}")
            toml={}


    # Second pass at command line
    parser = argparse.ArgumentParser(
        parents=[parser],
        prog="owpost",
        description="Log 1-wire data externally to protect interior sensors. Transmittter component",
        epilog="By Paul H Alfille 2025 -- repository: https://github.com/alfille/owlogger")

    # token
    parser.add_argument('-t','--token',
        required=False,
        default=toml.get("token",argparse.SUPPRESS),
        dest="token",
        type=str,
        nargs='?',
        help='Secret token to authentificate message (optonal arbitrary text string)'
        )

    # Server address
    default_port = 8001
    server = f"localhost:{default_port}"
    parser.add_argument('-s','--server',
        required=False,
        default=toml.get("server",server),
        dest="server",
        nargs='?',
        help=f'Server network address (optional) default={server}\t\nNote that this default is a local testing setup.'
        )
        
    # One-wire owserver address
    default_owport = 4304
    owserver = f"localhost:{default_owport}"
    parser.add_argument('-o','--owserver',
        required=False,
        default=toml.get("owserver",owserver),
        dest="owserver",
        nargs='?',
        help=f'owserver network address (optional) default={owserver}'
        )
        
    # Celsius
    parser.add_argument( "-C", "--Celsius",
        required=False,
        default=toml.get("Celsius",False),
        dest="Celsius",
        action = "store_true",
        help="Use Celsius temperature scale for readings. Default: Fahrenheit"
        )

    # Fahrenheit
    parser.add_argument( "-F", "--Fahrenheit",
        required=False,
        default=toml.get("Fahrenheit",True),
        dest="Fahrenheit",
        action = "store_true",
        help="Use Fahrenheit temperature scale for readings. Default: Fahrenheit"
        )
        
    # name
    parser.add_argument('-n','--name',
        required=False,
        default=toml.get("name","owpost"),
        dest="name",
        nargs='?',
        type=str,
        help=f'Optional name for data source. Default owpost'
        )
        
    # periodic
    parser.add_argument('-p','--period',
        required=False,
        default=toml.get("period",argparse.SUPPRESS),
        dest="period",
        nargs='?',
        type=int,
        help=f'Period (minutes) to repeat reading and sending (single-shot if not present)'
        )
        
    # debug output
    parser.add_argument('-d', '--debug', 
        required=False,
        default=toml.get("debug",False),
        action='store_true',
        dest="debug",
        help='debug output'
        )
        
        
    args=parser.parse_args()
    print(sysargs,args)

    #JWT token
    if "token" in args:
            secret = jwt.encode( {'name':args.name},args.token,algorithm='HS256')
    else:
        secret=None

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

    if args.Celsius or not args.Fahrenheit:
        temp_scale=protocol.FLG_TEMP_C
    else:
        temp_scale=protocol.FLG_TEMP_F

    #
    # create owserver proxy object
    #
    try:
        owproxy = protocol.proxy(
            owserver_host, owserver_port, 
            flags=temp_scale,
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
        try:
            owdir = owproxy.dir(slash=False, bus=False)
        except protocol.OwnetError:
            print( "Cannot read owserver" )
            owdir = []
        for sensor in owdir:
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
            upload( server, secret, "no data" )
        else:
            upload( server, secret, " ".join([temperature_string]) )

        if period==None:
            # single shot
            break

        # delay and repeat
        time.sleep( 60*period )
        

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
