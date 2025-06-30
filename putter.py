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
    j = json.dumps( {'data': data_string } )
    try:
        response = send_put(
            url,
            data = j ,
            headers = { "Content-Type": "application/text"}
            )
    except:
        print( datetime.datetime.now(), data_string ) 


upload("this is a test 1")
upload("this is a test 2")
upload("this is a test 2.2")
upload("this is a test 333")

