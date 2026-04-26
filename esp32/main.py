# ESP32 owpost program

import machine
import gc
import sys
import network
#import socket
import ntptime
import time
import json
import onewire
import ds18x20
import urequests

import tomli
import jwt

#----------
server = None
time.sleep(2) #for watchdog
wdt = machine.WDT(timeout=120000) #timeout
token_timeout = 60*60 #1hr
ntptime.host = "pool.ntp.org"
epoch_correction = 946684800
wifi_region = "US"
ntp.timeout(5)

class Transmit:
    def __init__(self, server, name, wifi, token):
        self.server = server
        self.name = name
        network.country(wifi_region)
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config( reconnects=3)
        
        self.wifi = wifi
        self.wifi_index = 0
        
        self.token = token
        self.goodtime = False
            
    def connect( self ):
        for j in range(0,10):
            for k in range(0,3):
                try:
                    print(f"Attempting wifi {self.wifi_index} {self.wifi[self.wifi_index]['ssid']}")
                    self.wlan.connect( self.wifi[self.wifi_index]['ssid'], self.wifi[self.wifi_index]['password'] )
                    for tries in range(0,10):
                        wdt.feed()
                        time.sleep(5)
                        if self.wlan.isconnected():
                            print(f"Network {self.wlan.ifconfig()}")
                            for i in range(0,10):
                                wdt.feed()
                                # set time, even if already set, to manage drift
                                try:
                                    ntptime.settime()
                                    time.sleep(2)
                                    self.goodtime = True # can fail later and still trust time
                                    wdt.feed()
                                    return
                                except Exception as e:
                                    print(f"NTP error {e}")
                            if self.goodtime:
                                print("NTP not reset")
                                return
                            print("NTP not set")
                            machine.reset()
                except Exception as e:
                    print(f"WIFI error {e}")
            self.wifi_index = (self.wifi_index + 1) % len(self.wifi)
        print("Cannot connect");
        
        machine.reset() # trigger wdt to reset
    
    def upload( self, data_string ):
        if not self.wlan.isconnected():
            self.connect()

        # JWT token?
        if self.token == None:
            self.headers = { "Content-Type": "application/text"}
        else:
            now = time.time() + epoch_correction
            secret = jwt.encode( {
                'name':self.name,
                'iat':now,
                'exp':now+token_timeout,
                },
                self.token,
                algorithm='HS256'
                )
            self.headers = { 'Authorization': f'Bearer {secret}', 'Content-Type': 'application/text'}
        data = json.dumps( {'data': data_string, 'name':self.name } )
        for i in range(0,3):
            if self.post(data):
                break
            self.connect()

    def post( self, data ):
        print(f"Sending {data}") 
        wdt.feed()
        response = None
        success = False
        try:
            response = urequests.post( self.server, data=data, headers=self.headers, timeout=20 )
            success = ( 200 <= response.status_code < 300 )
        except Exception as e:
            print( f"{data} to {self.server} Error: {e}" )
        finally:
            wdt.feed()
            if response is not None:
                response.close()
        return success
    
    def close( self ):
        try:
            self.wlan.disconnect()
        except Exception as e:
            print(f"Disconnect error {e}")

def read_toml():
    try:
        with open( "owesp32.toml", "rb" ) as c:
            toml = tomli.load(c)
    except Exception as e:
        print(f"Cannot open TOML configuration file: owesp32.toml Error: {e}")
        sys.exit(1)
    toml.setdefault('name'       ,'esp32' );
    toml.setdefault('pin'        , 12     );
    toml.setdefault('Fahrenheit' , True   );
    toml.setdefault('Celsius'    , False  );
    toml.setdefault('period'     , 15     );
    return toml

def run(toml):
    global server
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
        gc.collect()
        wdt.feed()
        temperatures = []
        for i in range(0,3):
            roms = ds.scan()
            if roms:
                ds.convert_temp()
                time.sleep_ms(750)
                temperatures=[ds.read_temp(rom) for rom in roms]
                if len(temperatures)>0:
                    break
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

def main():
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
    sys.exit(main())
else:
    print("Standalone program")
