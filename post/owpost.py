#!/usr/bin/env python3
# owpost.py
#
# owfs machine upload data to owlogger
#
# Paul H Alfille 2025
# MIT license

# Example from https://pytutorial.com/python-requestsput-complete-guide-for-http-put-requests/

from requests import post as send_post
from requests.exceptions import ConnectionError, Timeout
import json
import datetime
import argparse
from pyownet import protocol
import sys
import time
import tomllib
from urllib.parse import urlparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# for authentification
try:
    import jwt
except ImportError:
    logging.error("JWT module needs to be installed. Do 'pip install PyJWT' or 'apt install python3-jwt'")
    sys.exit(1)

class Transmit:
    def __init__(self, server, name, token):
        self.server = server
        self.name = name
        self.token = token
                    
    def upload( self, data_string ):
        data = json.dumps( {'data': data_string, 'name':self.name } )
        self.post( data )

    def post( self, data ): 
        # JWT token?
        if self.token == None:
            headers = { "Content-Type": "application/text"}
        else:
            secret = jwt.encode(
                {'name':self.name, 'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
                self.token,
                algorithm='HS256'
                )
            headers = { 'Authorization': f'Bearer {secret}', 'Content-Type': 'application/text'}

        try:
            response = send_post( self.server, data=data, headers=headers, timeout=10 )
            logging.debug( f"Return code={response.status_code} ({response.reason}) from {response.url}, tried {self.server}")
            response.raise_for_status() # Trap 4xx/5xx errors
        except ConnectionError:
            logging.warning(f"Could not connect to server at {self.server}")
        except Timeout:
            logging.warning("Server request timed out.")
        except Exception as e:
            logging.error(f"Unexpected transmission error: {e}")

def read_toml( config_path ):
    try:
        with open( config_path, "rb" ) as c:
            return tomllib.load(c)
    except tomllib.TOMLDecodeError as e:
        with open ( config_path, "rb" ) as c:
            contents = c.read()
        for lin in zip(range(1,200),contents.decode('utf-8').split("\n")):
            logging.info(f"{lin[0]:3d}. {lin[1]}")
        logging.error(f"Trouble reading configuration file {config_path} Error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logging.info(f"No TOML configuration file {config_path}")
        return {}
    except PermissionError:
        logging.error(f"Access to {config_path} denied.")
        sys.exit(1)    
    except Exception as e:
        logging.warning(f"TOML Error: {e}")
    return {}

def server_tuple( server_string, default_port ):
    """
    Parse 'host:port' or bare 'host' into (host, port).
    """
    if "://" not in server_string:
        u = urlparse(f"http://{server_string}")
    else:
        u = urlparse(server_string)
    host = u.hostname or "localhost"
    port = u.port or default_port
    return host, port


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

    # Process TOML to get those baseline values
    # TOML file
    toml = read_toml( args.config )

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
        help='Secret token to authentificate message (optonal arbitrary text string) Must match the owlogger token.'
        )

    # Server address
    default_port = 8001
    server = f"http://localhost:{default_port}"
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
        
    # message
    parser.add_argument('-m','--message',
        required=False,
        dest="message",
        nargs='+',
        help='Message to send instead of 1-wire data. Can be data from another source.'
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

    logging.root.setLevel(logging.DEBUG if args.debug else logging.INFO)
    logging.debug(f"sysargs={sysargs}, args={args}")
        
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

    # message entry skips 1-wire and periodic loop
    if "message" in args and args.message !=None:
        logging.info( f"Args Message: {' '.join(args.message)}" )
        server.upload(' '.join(args.message))
        return
    if "message" in toml and toml["message"] != None:
        logging.info( f"Toml Message: {' '.join(toml['message'])}" )
        server.upload(' '.join(toml["message"]))
        return

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
        logging.error(f"Unable to open connection to '{owaddr}:{owport} Error: {error}")
        sys.exit(1)
    except protocol.ProtocolError as error:
        logging.error(f"'{owaddr}:{owport}' not an owserver? Protocol Error: {error}")
        sys.exit(1)

    #period
    if "period" in args:
        period = args.period
        if period is None:
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
            logging.warning( f"Cannot read owserver Error: {e}" )
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
    logging.info("Intended to be a standalone program")
