#!/usr/bin/env python3
# owposttext.py
#
# any text upload data to owlogger
#
# Paul H Alfille 2025
# MIT license

# Example from https://pytutorial.com/python-requestsput-complete-guide-for-http-put-requests/

from requests import put as send_put, post as send_post
import json
import datetime
import argparse
import sys
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
        prog="owposttext",
        description="Log any data data externally to protect interior sensors. Transmittter component",
        epilog="By Paul H Alfille 2025 -- repository: https://github.com/alfille/owlogger")

    # text
    parser.add_argument('input',
        nargs='*',
        type=str,
        help='text to be sent to owlogger, Or use stdin (e.g. pipe)',
        )
    
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
        
    # name
    parser.add_argument('-n','--name',
        required=False,
        default=toml.get("name","owposttext"),
        dest="name",
        nargs='?',
        type=str,
        help=f'Optional name for data source. Default owposttext'
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

    if args.input:
        if debug:
            print("command line text")
        server.upload( ' '.join(args.input))
    else:
        if debug:
            print("stdin text")
        server.upload( sys.stdin.read().strip() )

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
