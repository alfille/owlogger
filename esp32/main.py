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
import ujwt

----------

class Transmit:
    def __init__(self, server, name, token):
        self.server = server
        self.name = name
        
        # JWT token?
        if token == None:
            self.headers = { "Content-Type": "application/text"}
        else:
            secret = ujwt.encode( {'name':self.name},token,algorithm='HS256')
            self.headers = { 'Authorization': f'Bearer {secret}', 'Content-Type': 'application/text'}
            
    def upload( self, data_string ):
        data = json.dumps( {'data': data_string, 'name':self.name } )
        self.post( data )

    def post( self, data ): 
        try:
            response = urequests.post( self.server, data=data, headers=self.headers )
        except Exception as e:
            print( f"{data} to {self.server} Error: {e}" ) 

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

def main(sysargs):
    # Look for a config file location (else default) 
    # read it in TOML format
    # Process TOML to get those baseline values
    # TOML file

    toml = read_toml()

    # Server (external data collector)
    # Take server string as is. Can be http, https or anything that the reverse proxy can manage (perhaps a branch)
	if 'server' in toml:
		if `token` in toml:
			server = Transmit( toml.server, toml.name, toml.token )
		else:
			server = Transmit( toml.server, toml.name, None )
	else:
		print("No server in TOML file")
		sys.exit(1)

    # temperature flag
    inC = toml.Celsius or not toml.Fahrenheit:
		
	# onewire
	ow = onewire.OneWire( machine.Pin(toml.pin))
	ds = ds18x20.DS18x20(ow)

    # Loop
    while True:
        # Get Temperatures
        no_data = True
        temperatures = []
        roms = ds.scan()
        ds.conver_temp()
        time.sleep_ms(750)
        temperatures=[ds.read_temp(rom) for rom in roms]
        if not inC:
			temperatures = [9*T/5+32 for T in temperatures]
        if len(temperatures)>0:
            temperature_string = " ".join([f"T {t:.2f}" for t in temperatures])
            no_data = False
            
        if no_data:
            server.upload( "no data" )
        else:
            server.upload( temperature_string )

        # delay and repeat
        time.sleep( 60*toml.period )
        

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
