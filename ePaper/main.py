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
        self.get_headers(toml)
        self.get_wifi(toml)
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config( reconnects=3)
        
        self.display = epaper75.EPD()
        
    def get_server( toml ):
        if 'server' in toml:
            self.server = toml['server'].strip()
            if self.server[-1] == '/':
                self.url = "{}7in5".format(self.server)
            else:
                self.url = "{}/7in5".format(self.server)
        else:
            print("No server in TOML file")
            sys.exit(1)
        
    def get_wifi( toml ):
        if 'wifi' in toml:
            self.wifi = toml['wifi']
            self.wifi_index = 0
        else:
            print("No wifi entries in TOML file")
            sys.exit(1)
        
    def get_headers( toml ):
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
                response.raw.readinto(display.buffer)
            else:
                self.error_screen("Status {} from {}".format(response.status_code,self.server))
        except Exception as e:
            self.error_screen("Error during stream: {}".format(e))        
        finally:
            if 'response' in locals():
                response.close()
            display.display()
            display.sleep()
            
    def error_screen(self, text ):
        display.fb.fill(1) 
        display.fb.rect(10, 10, 780, 460, 0) 
        display.fb.fill_rect(10, 10, 780, 60, 0)
        display.fb.text("OWLOGGER ePaper display", 280, 35, 1)
        if self.wlan.isconnected():
            display.fb.text("Device Status: CONNECTED", 30, 100, 0)
        else:
            display.fb.text("Device Status: NOT CONNECTED", 30, 100, 0)
        display.fb.text("Display Type: 7.5 Inch Monochrome", 30, 120, 0)
        display.fb.text(text, 30, 140, 0)

    
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
        display.sleep()

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
