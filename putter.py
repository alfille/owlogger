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
import owpy3

#url = "https://alfille.online/logger"
url = "http://localhost:8001"

def upload( data_string ):
    global token
    if token==None:
        j = json.dumps( {'data': data_string } )
    else:
        j = json.dumps( {'token':token, 'data': data_string } )

    try:
        response = send_put(
            url,
            data = j ,
            headers = { "Content-Type": "application/text"}
            )
    except:
        print( datetime.datetime.now(), data_string ) 

def main(sysargs):
    # Command line first
    parser = argparse.ArgumentParser(
        prog="1-wire Logger",
        description="Log 1-wire data externally to protect interior environment\nSensor and transmittter component",
        epilog="Repository: https://github.com/alfille/logger")

    # token list
    parser.add_argument('-t','--token',
        metavar="TOKEN",
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
        metavar="SERVER",
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
        metavar="OWSERVER",
        default=owserver,
        dest="owserver",
        nargs='?',
        help=f'owserver network address (optional) default={owserver}'
        )
        
    # periodic
    parser.add_argument('-o','--owserver',
        required=False,
        metavar="OWSERVER",
        default=argparse.SUPPRESS,
        dest="period",
        nargs='?',
        help=f'Period (minutes) to repeat reading and sending (single-shot if not present)'
        )
        
        
    args=parser.parse_args()
    print(sysargs,args)

    global token
    if "token" in args:
        token = args.tokens
    else:
        token = None

    global server
    server = args.server_activate

    if args.owserver.find("//")==-1:
        owserver = args.owserver.split("//")[1]
    else:
        owserver = args.owserver
    if owserver.find(":")==-1:
        owserver_port = default_owport
    else:
        (owserver, owserver_port) = owserver.split(":")

    global period
    if "period" in args:
        period = args.period
        if period == NaN:
            period = 30
    else:
        period = None
 
    while True:
        


if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
