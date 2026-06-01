# ESP32-C3 owlogger display

import os
import sys
import network
import time
import urequests
import ubinascii
import gc
import machine
from machine import Pin, SPI

import tomli
#import ubinascii

#import epaper75

#----------
time.sleep(2) #for watchdog
wdt = machine.WDT(timeout=120000) #timeout

class Get:
    WIFI_REGION = "US"
    BUFFER_SIZE = 48000 # 480 * 800 // 8

    def __init__(self ):
        self.buffer = None
        self.wlan = None
        self.process()
        self.close()

    def process( self ):
        self.display = EPD_7in5()
        self.display.init()

        if not self.get_toml():
            return
            
        if not self.get_server():
            return
        print("Server",self.server)
        wdt.feed()

        self.get_headers()
        print("got headers")
        wdt.feed()

        if not self.get_wifi():
            return
        print("got wifi list")
        wdt.feed()

        if not self.get_connection():
            return
        print("got lan")
        wdt.feed()
        
        if not self.get_buffer():
            self.buffer = None
            return
        print("got data")
        
        print("initialized display")
        wdt.feed()
        
        self.display.show_buffer(self.buffer)
        
        self.display.sleep()
        print("Screen!")
        
    def get_toml( self ):
        self.period = 15
        try:
            with open( "owepaper.toml", "rb" ) as c:
                toml = tomli.load(c)
                print("configuration",toml)
                self.period = toml.get("period", self.period )
                self.server = toml.get("server", None )
                self.wifi = toml.get("wifi", None )
                self.username = toml.get( "username", None )
                self.password = toml.get( "password", None )
                return True
        except Exception as e:
            print(f"Cannot open TOML configuration file: owepaper.toml Error: {e}")
            return False

    def get_period( self ):
        return self.period

    def get_server( self ):
        if self.server:
            if self.server[-1] == '/':
                self.url = "{}7in5".format(self.server)
            else:
                self.url = "{}/7in5".format(self.server)
            return True
        else:
            print("No server in TOML file")
            return False
        
    def get_wifi( self ):
        if self.wifi:
            self.wifi_index = 0
            return True
        else:
            print("No wifi entries in TOML file")
            return False
        
    def get_headers( self ):
        if self.username and self.password:
            auth_str = f"{self.username}:{self.password}"
            auth_b64 = ubinascii.b2a_base64(auth_str.encode()).decode()
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

    def get_connection( self ):
        network.country(self.WIFI_REGION)
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config( reconnects=3)
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
                            rssi = self.wlan.status('rssi')
                            print(f"Signal strength: {rssi} dBm")
                            return True
                except Exception as e:
                    print(f"WIFI error {e}")
            self.wifi_index = (self.wifi_index + 1) % len(self.wifi)
        print("Cannot connect to wifi");
        return False

    def stop_connection( self ):
        """Disconnect from WiFi"""
        if self.wlan:
            if self.wlan.isconnected():
                self.wlan.disconnect()
                print("WiFi disconnected")

    def get_buffer( self ):
        for attempt in range(0,4):
            self.buffer = None
            gc.collect() # clean up space
            wdt.feed()
            print(f"Attempting to get buffer {attempt+1}")
            try:
                response = urequests.get( self.url, headers=self.headers, timeout=15 )
                wdt.feed()
                self.buffer = response.content
                wdt.feed()
                response.close()

                if len(self.buffer) == self.BUFFER_SIZE:
                    print("Full size buffer!")
                    return True
                
                print(f"buffer received size incorrect {len(self.buffer)} not {self.BUFFER_SIZE}")
                self.buffer = None
            
            except Exception as e:
                print(f"Error fetching buffer: {type(e).__name__}: {e}")

        return False
            
    def error_screen(self, text ):
        self.display.fb.fill(1) 
        self.display.fb.rect(10, 10, 780, 460, 0) 
        self.display.fb.fill_rect(10, 10, 780, 60, 0)
        self.display.fb.text("OWLOGGER ePaper display", 280, 35, 1)
        if not self.wlan:
            self.display.fb.text("Device Status: EARLY FAIL", 30, 100, 0)            
        elif self.wlan.isconnected():
            self.display.fb.text("Device Status: CONNECTED", 30, 100, 0)
        else:
            self.display.fb.text("Device Status: NOT CONNECTED", 30, 100, 0)
        self.display.fb.text("Display Type: 7.5 Inch Monochrome", 30, 120, 0)
        self.display.fb.text(text, 30, 140, 0)
    
    def close( self ):
        wdt.feed()
        if not self.buffer:
            self.error_screen("No data received")
        self.stop_connection()
        self.display.sleep()

# Display controller commands
class EPD_7in5:
    # Commands
    DATA_START_TRANSMISSION_1 = 0x10
    DATA_START_TRANSMISSION_2 = 0x13
    DISPLAY_REFRESH = 0x12
    POWER_OFF = 0x02
    POWER_SET = 0x01
    POWER_ON = 0x04
    DEEP_SLEEP = 0x07 
    PANEL_SET = 0x00
    RESOLUTION_SET = 0x61
    DUAL_SPI = 0x15
    VCOM_AND_DATA = 0x50
    TCON_SET = 0x60
    WIDTH = 800
    HEIGHT = 480
    
    def __init__(self, use_busy=False):
        """Initialize display for remote buffer display"""
        self.use_busy = use_busy
        
        # Setup SPI
        self.spi = SPI(1, baudrate=4_000_000, polarity=0, phase=0,
                      sck=Pin(8), mosi=Pin(10))
        
        # Control pins
        self.cs = Pin(3, Pin.OUT, value=1)
        self.dc = Pin(5, Pin.OUT, value=0)
        self.rst = Pin(2, Pin.OUT, value=1)
        
        if self.use_busy:
            self.busy = Pin(4, Pin.IN)
        else:
            self.busy = None
        
        print("Display initialized for remote buffer")
    
    def reset(self):
        self.rst.value(1)
        time.sleep_ms(200)
        self.rst.value(0)
        time.sleep_ms(2)
        self.rst.value(1)
        time.sleep_ms(200)
        wdt.feed()

    def init(self):
        self.reset()
        self.wait_if_busy()
        
        self._command(self.POWER_SET) # Power Setting
        self._data_chunk([0x07, 0x07, 0x3f, 0x3f])
        
        self._command(self.POWER_ON) # Power ON
        self.wait_if_busy()
        
        self._command(self.PANEL_SET) # Panel Setting
        self._data_chunk([0x1F])    # KW-BF, KWR-AF, BWROTP
        
        self._command(self.RESOLUTION_SET) # Resolution setting
        self._data_chunk([0x03, 0x20, 0x01, 0xE0]) # 800x480
        
        self._command(self.DUAL_SPI) # Dual SPI mode
        self._data_chunk([0x00])
        
        self._command(self.VCOM_AND_DATA) # VCOM and Data Interval
        self._data_chunk([0x10, 0x07])
        
        self._command(self.TCON_SET) # TCON setting
        self._data_chunk([0x22])

    def _command(self, command):
        """Send command to display"""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([command]))
        self.cs.value(1)
    
    def _data_chunk(self, data):
        """Send data chunk to display"""
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray(data))
        self.cs.value(1)
    
    def wait_if_busy(self):
        """Wait for display if BUSY pin enabled"""
        if not self.use_busy or not self.busy:
            time.sleep_ms(2000)
            wdt.feed()
            return
        
        print("Waiting for display...", end='')
        count = 0
        while self.busy.value() == 1:
            time.sleep_ms(100)
            count += 1
            if count % 10 == 0:
                print(".", end='')
                wdt.feed()
            if count >= 400:  # 40 second timeout
                print(" TIMEOUT!")
                return
        print(" Ready!")
    
    def show_buffer(self, buf):
        print("Sending buffer to display...")
        
        # Send old image (white)
        print("  Clearing old image...")
        self._command(self.DATA_START_TRANSMISSION_1)
        white_line = bytearray([0xFF] * self.WIDTH // 8)
        for _ in range(self.HEIGHT):  # 48000 / 100
            self._data_chunk(white_line)
        wdt.feed()
        
        # Send new image
        print("  Transferring image buffer...")
        self._command(self.DATA_START_TRANSMISSION_2)
        
        # Send in chunks to avoid memory issues
        chunk_size = 1024  # 1KB chunks
        for i in range(0, len(buf), chunk_size):
            chunk = buf[i:i+chunk_size]
            self._data_chunk(chunk)
            # Yield to avoid watchdog timeout
            if i % 10240 == 0:  # Every ~10 chunks
                time.sleep_ms(1)
                wdt.feed()
        
        # Trigger refresh
        print("  Refreshing display...")
        self._command(self.DISPLAY_REFRESH)
        self.wait_if_busy()
        
        print("Display updated!")
        return True

    def sleep(self):
        self._command(self.POWER_OFF) # Power Off
        self.wait_if_busy()
        self._command(self.DEEP_SLEEP) # Deep Sleep
        self._data_chunk([0xA5])


def main(sysargs):
    # Look for a config file location (else default) 
    # read it in TOML format
    # Process TOML to get those baseline values
    # TOML file

    wdt.feed()
    print("Starting")

    try:
        retriever = Get()
        machine.deepsleep( retriever.get_period()*60*1000 ) # 2 minutes
    except KeyboardInterrupt:
        machine.deepsleep( 60*1000 ) # 1 minute

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
