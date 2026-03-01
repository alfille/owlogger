# ESP32 owpost program

import machine
import os
import sys
import network
import time
import json
import onewire
import ds18x20
import urequests

import tomli
import hmac
import jwt

#----------
server = None
time.sleep(2) #for watchdog
wdt = machine.WDT(timeout=10000) #timeout

class Transmit:
    def __init__(self, server, name, wifi, token):
        self.server = server
        self.name = name
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config( reconnects=3)
        
        self.wifi = wifi
        self.wifi_index = 0

        # JWT token?
        if token == None:
            self.headers = { "Content-Type": "application/text"}
        else:
            secret = jwt.encode( {'name':self.name},token,algorithm='HS256')
            self.headers = { 'Authorization': f'Bearer {secret}', 'Content-Type': 'application/text'}
            
    def connect( self ):
        while True:
            try:
                print(f"Attempting wifi {self.wifi_index} {self.wifi[self.wifi_index]['ssid']} / {self.wifi[self.wifi_index]['password']}")
                self.wlan.connect( self.wifi[self.wifi_index]['ssid'], self.wifi[self.wifi_index]['password'] )
                for tries in range(0,10):
                    wdt.feed()
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
        wdt.feed()
        try:
            response = urequests.post( self.server, data=data, headers=self.headers )
            print("Sent")
            success = True
        except Exception as e:
            print( f"{data} to {self.server} Error: {e}" )
            success = False ;
        finally:
            wdt.feed()
            response.close()
        return success
    
    def close( self ):
        try:
            self.wlan.disconnect()
        except Exception as e:
            print(f"Disconnect error {e}")
        self.wlan.active(False)

def read_toml():
    try:
        with open( "owesp32.toml", "rb" ) as c:
            toml = tomli.load(c)
    except Exception as e:
        print(f"Cannot open TOML configuration file: owesp32.toml Error: {e}")
        sys.exit(1)
    toml.setdefault('name'       ,'esp32' );
    toml.setdefault('pin'        ,'12'    );
    toml.setdefault('Fahrenheit' , True   );
    toml.setdefault('Celsius'    , False  );
    toml.setdefault('period'     , 15     );
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
        
    # temperature flag
    inC = (toml['Celsius']) or (not toml['Fahrenheit'])
        

    # onewire
    wdt.feed()
    try:
        ow = onewire.OneWire( machine.Pin(toml['pin']))
        ds = ds18x20.DS18X20(ow)
    except Exception as e:
        print(f"Onewire connection problem ERROR: {e}" )
        sys.exit(1)

    # Loop
    while True:
        # Get Temperatures
        temperatures = []
        roms = ds.scan()
        print(roms);
        wdt.feed()
        ds.convert_temp()
        time.sleep_ms(750)
        wdt.feed()
        temperatures=[ds.read_temp(rom) for rom in roms]
        if not inC:
            # Farhenheit conversion
            temperatures = [9*T/5+32 for T in temperatures]
        if len(temperatures)>0:
            server.upload( " ".join([f"T {t:.2f}" for t in temperatures]) )
        else:
            server.upload( "no data" )

        # delay and repeat
        for _ in range(60*toml['period'] ):
            wdt.feed()
            time.sleep(1)

def main(sysargs):
    # Look for a config file location (else default) 
    # read it in TOML format
    # Process TOML to get those baseline values
    # TOML file

    wdt.feed()
    toml = read_toml()
    wdt.feed()
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
