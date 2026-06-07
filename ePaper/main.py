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

#----------
time.sleep(2) #for watchdog
wdt = machine.WDT(timeout=120000) #timeout

class Get:
    WIFI_REGION = "US"

    def __init__(self ):
        self.buffer = None
        self.wlan = None
        self.process()
        self.close()

    def process( self ):
        if not self.get_toml():
            return
            
        self.display = EPD_7in5( self.width, self.height )
        self.display.init()

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
        
        self.display.deep_sleep()
        print("Screen!")
        
    def get_toml( self ):
        try:
            with open( "owepaper.toml", "rb" ) as c:
                toml = tomli.load(c)
                print("configuration",toml)
                self.period = toml.get("period", 15 ) # default 15 minutes
                self.server = toml.get("server", None )
                self.wifi = toml.get("wifi", None )
                self.username = toml.get( "username", None )
                self.password = toml.get( "password", None )
                self.width = toml.get( "width", 800 ) # default 800x480 screen
                self.height = toml.get( "height", 480 ) #
                
                return True
        except Exception as e:
            print(f"Cannot open TOML configuration file: owepaper.toml Error: {e}")
            return False

    def get_period( self ):
        return self.period

    def get_server( self ):
        if self.server:
            if self.server[-1] == '/':
                self.url = f"{self.server}ePaper"
            else:
                self.url = f"{self.server}/ePaper"
            print("URL",self.url)
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
            auth_b64 = ubinascii.b2a_base64(auth_str.encode()).decode().strip()
            self.headers = {
                "Authorization": f"Basic {auth_b64}",
                "Accept": "image/x-raw",
                "Connection": "close"
            }
        else:
            self.headers = {
                "Accept": "image/x-raw",
                "Connection": "close"
            }
            print("No username / password")
        print( "HEADER",self.headers )

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
                response = urequests.get( f"{self.url}?width={self.width}&height={self.height}", headers=self.headers, timeout=15 )
                wdt.feed()
                self.buffer = response.content
                wdt.feed()
                response.close()

                if len(self.buffer) == self.width * self.height // 8:
                    print("Full size buffer!")
                    return True
                
                print(f"buffer received size incorrect {len(self.buffer)} not {self.width * self.height // 8}")
                print( self.buffer )
                self.buffer = None
            
            except Exception as e:
                print(f"Error fetching buffer: {type(e).__name__}: {e}")

        return False
            
    def error_screen(self, text ):
        return
    
    def close( self ):
        wdt.feed()
        if not self.buffer:
            self.error_screen("No data received")
        self.stop_connection()
        self.display.deep_sleep()

# Display controller commands
class EPD_7in5:
    # Commands to Seedstudio ePaper controller, equivalent to UltraChip UC8179
    DATA_START_TRANSMISSION_1 = 0x10
    DATA_START_TRANSMISSION_2 = 0x13
    DISPLAY_REFRESH = 0x12
    POWER_OFF = 0x02
    POWER_SET = 0x01
    POWER_ON = 0x04
    DEEP_SLEEP = 0x07 
    PANEL_SET = 0x00
    RESOLUTION_SET = 0x61
    BOOSTER_SOFT = 0x06
    DUAL_SPI = 0x15
    VCOM_AND_DATA = 0x50
    TCON_SET = 0x60
    DATA_ENTRY = 0x11
    RAM_X_SET = 0x44
    RAM_Y_SET = 0x45
    COUNTER_X_SET = 0x4E
    COUNTER_Y_SET = 0x4F
    
    def __init__(self, width=800, height=480):
        """Initialize display for remote buffer display"""
        self.width = width
        self.height = height
        
        # Setup SPI
        self.spi = SPI(1, baudrate=4_000_000, polarity=0, phase=0,
                      sck=Pin(8), mosi=Pin(10))
        
        # Control pins
        self.cs = Pin(3, Pin.OUT, value=1)
        self.dc = Pin(5, Pin.OUT, value=0)
        self.rst = Pin(2, Pin.OUT, value=1)
        self.busy = Pin(4, Pin.IN)
        
        print("Display initialized for remote buffer")
    
    def _reset(self):
        # ~ self.rst.value(1)
        # ~ time.sleep_ms(200)
        self.rst.value(0)
        time.sleep_ms(200)
        self.rst.value(1)
        time.sleep_ms(200)
        wdt.feed()

    def init(self):
        self._reset()
        self._wait_if_busy()
        
        self._command( self.BOOSTER_SOFT )
        self._data_send([0x17, 0x17, 0x1E, 0x17])
        
        self._command(self.POWER_SET) # Power Setting
        self._data_send([0x07, 0x07, 0x3f, 0x3f])
        
        self._command(self.POWER_ON) # Power ON
        self._wait_if_busy()
        
        self._command(self.PANEL_SET) # Panel Setting
        self._data_send([0x1F])    # KW-BF, KWR-AF, BWROTP
        
        self._command(self.RESOLUTION_SET) # Resolution setting
        self._data_send(list(self.width.to_bytes(2,'big')))
        self._data_send(list(self.height.to_bytes(2,'big')))
        
        #self._command(self.DUAL_SPI) # Dual SPI mode
        #self._data_send([0x00])
        
        self._command(self.VCOM_AND_DATA) # VCOM and Data Interval
        self._data_send([0x10, 0x14])
        
        #self._command(self.TCON_SET) # TCON setting
        #self._data_send([0x22])

    def _command(self, command):
        """Send command to display"""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([command]))
        self.cs.value(1)
    
    def _data_send(self, data):
        """Send data chunk to display"""
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray(data))
        self.cs.value(1)
    
    def _mv_send(self, data):
        """Send memoryview chunk to display"""
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)
    
    def _wait_if_busy(self):
        """Wait for display if BUSY pin enabled"""
        count = 0
        #print(f"{count}. BUSY={self.busy.value()}")
        while self.busy.value() == 0:
            time.sleep_ms(100)
            count += 100
            #print(f"{count}. BUSY={self.busy.value()}")
            wdt.feed()
            if count >= 12000:  # 12 second timeout limit
                break
                
    def _display_refresh(self):
        time.sleep_ms(10)
        self._command(self.DISPLAY_REFRESH)
        self._wait_if_busy()
            
    def _clear( self, byte ):
        self._command(self.DATA_START_TRANSMISSION_1)
        line = self.width // 8
        white_line = bytearray([byte] * line ) # self.WIDTH // 8
        for _ in range(self.height):
            self._data_send(white_line)
            wdt.feed()
        

    def show_buffer(self, screen_buf):
        print("Sending buffer to display...")
        
        buf = memoryview(screen_buf)
        
        w_byte = 0xFF
        b_byte = 0x00
        
        # Full clear cycle to eliminate ghosting
        self._clear(0x00)          # black to old frame
        self._display_refresh()

        self._clear(0xFF)          # white to old frame  
        self._display_refresh()

        # Load white into old frame (DTM1)
        self._clear(0xFF)

        # Send new image
        print("  Transferring image buffer...")
        self._command(self.DATA_START_TRANSMISSION_2)
        
        # Send in chunks to avoid memory issues
        line = self.width // 8
        length = line * self.height
        for n in range(0, length, line):
            self._mv_send(buf[n:n+line])
            # Yield to avoid watchdog timeout
            wdt.feed()
        
        # Trigger refresh
        print("  Refreshing display...")
        self._display_refresh()
        
        print("Display updated!")
        return True

    def deep_sleep(self):
        print("Prepare to power down the screen")
        self._command(self.POWER_OFF) # Power Off
        self._wait_if_busy()
        print("Screen sleep")        
        self._command(self.DEEP_SLEEP) # Deep Sleep
        self._data_send([0xA5])


def main(sysargs):
    # Look for a config file location (else default) 
    # read it in TOML format
    # Process TOML to get those baseline values
    # TOML file

    wdt.feed()
    print("Starting")

    try:
        retriever = Get()
        print("Primary deepsleep")
        machine.deepsleep( retriever.get_period()*60*1000 ) # 2 minutes
    except KeyboardInterrupt:
        print("Backup deepsleep")
        machine.deepsleep( 15*60*1000 ) # 15 minute

if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
