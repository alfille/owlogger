# ESP32-C3 owlogger display

import machine
import os
import sys
import network
import time
import json
import urequests

import tomli
import hmac
import jwt

#----------
server = None

class Transmit:
    def __init__(self, server, name, wifi, token):
        self.server = server
        self.name = name
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config( reconnects=3)
        
        self.wifi = wifi
        self.wifi_index = 0
            
    def connect( self ):
        while True:
            try:
                print(f"Attempting wifi {self.wifi_index} {self.wifi[self.wifi_index]['ssid']} / {self.wifi[self.wifi_index]['password']}")
                self.wlan.connect( self.wifi[self.wifi_index]['ssid'], self.wifi[self.wifi_index]['password'] )
                for tries in range(0,10):
                    time.sleep(1)
                    if self.wlan.isconnected():
                        print(f"Network {self.wlan.ifconfig()}")
                        return
            except Exception as e:
                print(f"WIFI error {e}")
            self.wifi_index = (self.wifi_index + 1) % len(self.wifi)
    
    def upload( self, data_string ):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.connect()
        data = json.dumps( {'data': data_string, 'name':self.name } )
        while not self.post(data):
            self.connect()
        self.wlan.active(False)

    def post( self, data ):
        print(f"Sending {data}") 
        try:
            response = urequests.post( self.server, data=data, headers=self.headers )
        except Exception as e:
            print( f"{data} to {self.server} Error: {e}" )
            return False ;
        return True
    
    def close( self ):
        try:
            self.wlan.disconnect()
        except Exception as e:
            print(f"Disconnect error {e}")
        self.wlan.active(False)

def read_toml():
    try:
        with open( "owepaper.toml", "rb" ) as c:
            toml = tomli.load(c)
    except Exception as e:
        print(f"Cannot open TOML configuration file: owepaper.toml Error: {e}")
        sys.exit(1)
    toml.setdefault('username'   ,'user'  )
    toml.setdefault('password'   ,'pass'  )
    toml.setdefault('period'     , 30     )
    return toml

def run(toml):
    if 'wifi' not in toml:
        print("No Wifi settings in TOML file")
        sys.exit(1)

    # Server (external data collector)
    # Take server string as is. Can be http, https or anything that the reverse proxy can manage (perhaps a branch)
    if 'server' in toml:
        if 'token' in toml:
            server = Transmit( toml['server'], toml['name'], toml['wifi'], toml['token'] )
        else:
            server = Transmit( toml['server'], toml['name'], toml['wifi'], None )
    else:
        print("No server in TOML file")
        sys.exit(1)
        
    # Loop
    while True:
        # delay and repeat
        time.sleep( 60*toml['period'] )

def main(sysargs):
    # Look for a config file location (else default) 
    # read it in TOML format
    # Process TOML to get those baseline values
    # TOML file

    toml = read_toml()
    print("configuration",toml)

    try:
        run(toml)
    except KeyboardInterrupt:
        if server:
            server.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
