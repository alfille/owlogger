# ESP32-C3 owlogger display

import os
import sys
import network
import time
import urequests
import gc

import tomli
import ubinascii

import epaper75

#----------
getter = None

class Get:
    def __init__(self, toml ):
        self.get_server(toml)
        print("Server",self.server)
        self.get_headers(toml)
        print("got headers")
        self.get_wifi(toml)
        print("got wifi")
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config( reconnects=3)
        print("got lan")
        
        self.display = epaper75.EPD()
        self.display.init()
        print("initialized display")
        
        self.error_screen("Startup")
        self.display.display()
        self.display.sleep()
        print("Screen!")
        
    def get_server( self, toml ):
        if 'server' in toml:
            self.server = toml['server'].strip()
            if self.server[-1] == '/':
                self.url = "{}7in5".format(self.server)
            else:
                self.url = "{}/7in5".format(self.server)
        else:
            print("No server in TOML file")
            sys.exit(1)
        
    def get_wifi( self, toml ):
        if 'wifi' in toml:
            self.wifi = toml['wifi']
            self.wifi_index = 0
        else:
            print("No wifi entries in TOML file")
            sys.exit(1)
        
    def get_headers( self, toml ):
        if ('username' in toml) and ('password' in toml):
            auth_str = "{}:{}".format(toml['username'], toml['password'])
            auth_b64 = ubinascii.b2a_base64(auth_str.encode()).decode().strip()
            self.headers = {
                "Authorization": "Basic " + auth_b64,
                "Accept": "application/octet-stream",
                "Connection": "close"
            }
        else:
            self.headers = {
                "Accept": "application/octet-stream",
                "Connection": "close"
            }
            print("No username / passord")
        
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
    
    def download( self ):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.connect()
        gc.collect()
        try:
            response = urequests( url, stream = True, headers = self.headers )
            print( "Status code:", response.status_code)
            if response.status_code == 200:
                response.raw.readinto(self.display.buffer)
            else:
                self.error_screen("Status {} from {}".format(response.status_code,self.server))
        except Exception as e:
            self.error_screen("Error during stream: {}".format(e))        
        finally:
            if 'response' in locals():
                response.close()
            self.display.display()
            self.display.sleep()
            
    def error_screen(self, text ):
        self.display.fb.fill(1) 
        self.display.fb.rect(10, 10, 780, 460, 0) 
        self.display.fb.fill_rect(10, 10, 780, 60, 0)
        self.display.fb.text("OWLOGGER ePaper display", 280, 35, 1)
        if self.wlan.isconnected():
            self.display.fb.text("Device Status: CONNECTED", 30, 100, 0)
        else:
            self.display.fb.text("Device Status: NOT CONNECTED", 30, 100, 0)
        self.display.fb.text("Display Type: 7.5 Inch Monochrome", 30, 120, 0)
        self.display.fb.text(text, 30, 140, 0)
    
    def close( self ):
        try:
            self.wlan.disconnect()
        except Exception as e:
            print(f"Disconnect error {e}")
        self.wlan.active(False)
        self.display.sleep()

def read_toml():
    try:
        with open( "owepaper.toml", "rb" ) as c:
            toml = tomli.load(c)
    except Exception as e:
        print(f"Cannot open TOML configuration file: owepaper.toml Error: {e}")
        sys.exit(1)
    toml.setdefault('period'     , 30     )
    return toml

def header(toml):
    auth_str = "{}:{}".format(toml['username'], toml['password'])
    auth_b64 = ubinascii.b2a_base64(auth_str.encode()).decode().strip()
    headers = {
        "Authorization": "Basic " + auth_b64
    }
    return headers
    
def run(toml):
    getter = Get(toml)

    # Loop
    while True:
        getter.download()
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
        if getter:
            getter.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
