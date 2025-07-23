#!/usr/bin/env python3
# putter.py
#
# owfs machine upload data
#
# Paul H Alfille 2025
# MIT license

# Example from https://pytutorial.com/python-requestsput-complete-guide-for-http-put-requests/

from requests import put as send_put, post as send_post
import json
import datetime
import argparse
import math
from pyownet import protocol
import sys
import time
import tomllib
import urllib
from urllib.parse import urlparse

# for authentification
try:
    import jwt
except:
    print("JWT module needs to be installed")
    print("either 'pip install PyJWT' or 'apt install python3-jwt'")
    sys.exit(1)

class Transmit:
    def __init__(self, server, name, token):
        self.server = server
        self.name = name
        
        # JWT token?
        if token == None:
            self.headers = { "Content-Type": "application/text"}
        else:
            secret = jwt.encode( {'name':self.name},token,algorithm='HS256')
            self.headers = { 'Authorization': f'Bearer {secret}', 'Content-Type': 'application/text'}
            
    def upload( self, data_string ):
        data = json.dumps( {'data': data_string, 'name':self.name } )
        self.post( data )

    def post( self, data ): 
        try:
            response = send_post( self.server, data=data, headers=self.headers )
            global debug
            if debug:
                print( f"Return code={response.status_code} ({response.reason}) from {response.url}, tried {self.server}")
        except Exception as e:
            print( f"{datetime.datetime.now()}, {data} to {self.server} Error: {e}" ) 

def read_toml( args ):
    if "config" in args:
        try:
            with open( args.config, "rb" ) as c:
                toml = tomllib.load(c)
        except tomllib.TOMLDecodeError as e:
            with open ( args.config, "rb" ) as c:
                contents = c.read()
            for lin in zip(range(1,200),contents.decode('utf-8').split("\n")):
                print(f"{lin[0]:3d}. {lin[1]}")
            print(f"Trouble reading configuration file {args.config} Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Cannot open TOML configuration file: {args.config} Error: {e}")
            toml={}
    return toml

def server_tuple( server_string, default_port ):
    # takes a server string in a variety of formats and returns the bare needed components
    
    # Handle server address
    server = server_string
    
    # Add http:// for url processing even though it's not poart of the final result
    if server.find("//") == -1:
        server = f"http://{server}"
    
    # url parse and extract port
    u = urllib.parse.urlparse(server)
    port = u.port
    if port==None:
        port = default_port
        
    # netloc can include port, so remove 
    netloc = u.netloc.split(':')[0]
    
    return netloc, port

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
    toml = read_toml( args )

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

    #server
    # debug
    global debug
    debug = args.debug
    if debug:
        print("Debugging on")
        
    # Server (external data collector)
    # Take server string as is. Can be http, https or anything that the reverse proxy can manage (perhaps a branch)
    if "token" in args:
        server = Transmit( args.server, args.name, args.token )
    else:
        server = Transmit( args.server, args.name, None )

    # temperature flag
    if args.Celsius or not args.Fahrenheit:
        temp_scale=protocol.FLG_TEMP_C
    else:
        temp_scale=protocol.FLG_TEMP_F

    #
    # create owserver proxy object
    #
    (owaddr,owport) = server_tuple( args.owserver, default_owport )
    try:
        owproxy = protocol.proxy(
            owaddr, owport, 
            flags=temp_scale,
            verbose=args.debug, )
    except protocol.ConnError as error:
        print(f"Unable to open connection to '{owaddr}:{owport} Error: {error}")
        sys.exit(1)
    except protocol.ProtocolError as error:
        print("'{owaddr}:{owport}' not an owserver? Protocol Error: {error}")
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
        except protocol.OwnetError as e:
            print( "Cannot read owserver Error: {e}" )
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
            server.upload( "no data" )
        else:
            server.upload( " ".join([temperature_string]) )

        if period==None:
            # single shot
            break

        # delay and repeat
        time.sleep( 60*period )
        

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
