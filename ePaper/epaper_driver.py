"""
MicroPython driver for Seeed Studio 7.5" ePaper Display
Using the Seeed Studio ePaper Driver Board with XIAO

Hardware:
- XIAO ESP32-C3 (or other XIAO board) plugged into ePaper Driver Board
- 7.5" Monochrome ePaper (800x480) connected via 24-pin FPC connector

The driver board handles all the pin connections automatically when you plug
the XIAO into the socket. The pins are pre-wired on the driver board.

For XIAO ESP32-C3/ESP32-S3 on ePaper Driver Board:
- SPI MOSI: GPIO10 (D10)
- SPI CLK: GPIO8 (D8)
- CS: GPIO3 (D3)
- DC: GPIO5 (D5)
- RST: GPIO2 (D2)
- BUSY: GPIO4 (D4)

Battery: Can be connected to JST connector with power switch
"""

from machine import Pin, SPI
import time
import framebuf

class EPD_7in5:
    """Driver for 7.5 inch ePaper display (800x480 resolution)"""
    
    # Display resolution
    WIDTH = 800
    HEIGHT = 480
    
    # Display commands (for most common 7.5" ePaper controllers)
    PANEL_SETTING = 0x00
    POWER_SETTING = 0x01
    POWER_OFF = 0x02
    POWER_ON = 0x04
    BOOSTER_SOFT_START = 0x06
    DEEP_SLEEP = 0x07
    DATA_START_TRANSMISSION_1 = 0x10
    DATA_STOP = 0x11
    DISPLAY_REFRESH = 0x12
    DATA_START_TRANSMISSION_2 = 0x13
    VCOM_AND_DATA_INTERVAL_SETTING = 0x50
    RESOLUTION_SETTING = 0x61
    
    def __init__(self):
        """Initialize the ePaper display using driver board pinout"""
        print("Initializing ePaper with Driver Board...")
        
        # Setup SPI - XIAO ePaper Driver Board uses SPI1
        # MOSI=GPIO10, CLK=GPIO8
        self.spi = SPI(1, 
                      baudrate=4000000,
                      polarity=0, 
                      phase=0,
                      sck=Pin(8),   # D8 - CLK
                      mosi=Pin(10), # D10 - MOSI (DIN)
                      miso=None)    # Not used for ePaper
        
        # Setup control pins - these are pre-wired on the driver board
        self.cs = Pin(3, Pin.OUT)    # D3 - Chip Select
        self.dc = Pin(5, Pin.OUT)    # D5 - Data/Command
        self.rst = Pin(2, Pin.OUT)   # D2 - Reset
        self.busy = Pin(4, Pin.IN)   # D4 - Busy
        
        # Set initial states
        self.cs.value(1)  # CS high (inactive)
        
        # Display dimensions
        self.width = self.WIDTH
        self.height = self.HEIGHT
        
        # Create framebuffer (1 bit per pixel, monochrome)
        self.buffer = bytearray(self.width * self.height // 8)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, 
                                            self.height, framebuf.MONO_HLSB)
        
        # Initialize display
        self.init()
    
    def _command(self, command):
        """Send command to display"""
        self.dc.value(0)  # Command mode
        self.cs.value(0)  # Select display
        self.spi.write(bytearray([command]))
        self.cs.value(1)  # Deselect
    
    def _data(self, data):
        """Send data to display"""
        self.dc.value(1)  # Data mode
        self.cs.value(0)  # Select display
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)  # Deselect
    
    def wait_until_idle(self):
        """Wait until the display is ready (BUSY pin goes LOW)"""
        print("Waiting for display...", end='')
        timeout = 400  # 40 seconds max
        while self.busy.value() == 1:  # HIGH = busy
            time.sleep_ms(100)
            timeout -= 1
            if timeout == 0:
                print(" TIMEOUT!")
                break
        print(" Ready")
    
    def reset(self):
        """Hardware reset"""
        self.rst.value(1)
        time.sleep_ms(20)
        self.rst.value(0)
        time.sleep_ms(2)
        self.rst.value(1)
        time.sleep_ms(20)
    
    def init(self):
        """Initialize display"""
        print("Initializing ePaper display...")
        self.reset()
        
        self.wait_until_idle()
        
        # Power setting
        self._command(self.POWER_SETTING)
        self._data(0x07)
        self._data(0x07)
        self._data(0x3f)
        self._data(0x3f)
        
        # Power on
        self._command(self.POWER_ON)
        time.sleep_ms(100)
        self.wait_until_idle()
        
        # Panel setting
        self._command(self.PANEL_SETTING)
        self._data(0x1f)  # KW-3f, KWR-2F, BWROTP 0f, BWOTP 1f
        
        # Set resolution
        self._command(self.RESOLUTION_SETTING)
        self._data(0x03)  # 800 (0x320)
        self._data(0x20)
        self._data(0x01)  # 480 (0x1E0)
        self._data(0xE0)
        
        # VCOM and data interval
        self._command(self.VCOM_AND_DATA_INTERVAL_SETTING)
        self._data(0x10)
        self._data(0x07)
        
        print("ePaper display initialized successfully!")
    
    def clear(self, color=0xFF):
        """Clear the display (0xFF=white, 0x00=black)"""
        print("Clearing display...")
        
        # Clear old image
        self._command(self.DATA_START_TRANSMISSION_1)
        for _ in range(self.width * self.height // 8):
            self._data(color)
        
        # Clear new image
        self._command(self.DATA_START_TRANSMISSION_2)
        for _ in range(self.width * self.height // 8):
            self._data(color)
        
        # Refresh
        self._command(self.DISPLAY_REFRESH)
        time.sleep_ms(100)
        self.wait_until_idle()
        print("Display cleared")
    
    def display(self):
        """Update the display with framebuffer contents"""
        print("Updating display...")
        
        # Send old image (for clean refresh)
        self._command(self.DATA_START_TRANSMISSION_1)
        for _ in range(self.width * self.height // 8):
            self._data(0xFF)
        
        # Send new image
        self._command(self.DATA_START_TRANSMISSION_2)
        self._data(self.buffer)
        
        # Trigger refresh
        self._command(self.DISPLAY_REFRESH)
        time.sleep_ms(100)
        self.wait_until_idle()
        print("Display updated!")
    
    def sleep(self):
        """Put display into deep sleep mode (saves power)"""
        print("Entering sleep mode...")
        self._command(self.DEEP_SLEEP)
        self._data(0xA5)
        time.sleep_ms(2000)
        print("Display sleeping")
    
    # Drawing methods (delegate to framebuffer)
    def fill(self, color):
        """Fill entire display (0=black, 1=white)"""
        self.framebuf.fill(color)
    
    def pixel(self, x, y, color):
        """Set pixel at (x,y)"""
        self.framebuf.pixel(x, y, color)
    
    def hline(self, x, y, width, color):
        """Draw horizontal line"""
        self.framebuf.hline(x, y, width, color)
    
    def vline(self, x, y, height, color):
        """Draw vertical line"""
        self.framebuf.vline(x, y, height, color)
    
    def line(self, x1, y1, x2, y2, color):
        """Draw line from (x1,y1) to (x2,y2)"""
        self.framebuf.line(x1, y1, x2, y2, color)
    
    def rect(self, x, y, width, height, color, fill=False):
        """Draw rectangle"""
        if fill:
            self.framebuf.fill_rect(x, y, width, height, color)
        else:
            self.framebuf.rect(x, y, width, height, color)
    
    def text(self, string, x, y, color=0):
        """Draw text (built-in 8x8 font)"""
        self.framebuf.text(string, x, y, color)


# Battery monitoring for driver board
class BatteryMonitor:
    """Monitor battery voltage on ePaper Driver Board"""
    
    def __init__(self):
        # Battery voltage divider on GPIO1 (A0)
        self.voltage_pin = Pin(1, Pin.IN)
        # ADC enable on GPIO6 (A5)
        self.adc_enable = Pin(6, Pin.OUT)
        self.adc_enable.value(1)  # Enable ADC
        
    def read_voltage(self):
        """Read battery voltage"""
        from machine import ADC
        adc = ADC(self.voltage_pin)
        adc.atten(ADC.ATTN_11DB)  # Full range: 0-3.3V
        adc_value = adc.read()
        # Driver board has voltage divider
        voltage = (adc_value / 4095.0) * 7.16
        return voltage


# Demo functions
def demo_hello_world():
    """Simple Hello World demo"""
    print("\n=== Hello World Demo ===")
    epd = EPD_7in5()
    
    # Clear to white
    epd.clear()
    
    # Draw text
    epd.fill(1)  # White background
    epd.text("Hello from Seeed Studio!", 50, 50, 0)
    epd.text("7.5 inch ePaper Display", 50, 70, 0)
    epd.text("with Driver Board", 50, 90, 0)
    epd.text("800x480 Resolution", 50, 110, 0)
    
    # Draw border
    epd.rect(0, 0, 800, 480, 0)
    epd.rect(5, 5, 790, 470, 0)
    
    # Update display
    epd.display()
    
    return epd


def demo_dashboard():
    """Info dashboard demo"""
    print("\n=== Dashboard Demo ===")
    epd = EPD_7in5()
    
    epd.fill(1)  # White background
    
    # Title bar
    epd.rect(0, 0, 800, 50, 0, fill=True)
    epd.text("HOME AUTOMATION DASHBOARD", 200, 20, 1)
    
    # Three info boxes
    # Box 1 - Temperature
    epd.rect(20, 70, 240, 150, 0)
    epd.text("Temperature", 30, 80, 0)
    epd.text("Living Room", 30, 100, 0)
    epd.text("22.5 C", 60, 140, 0)
    
    # Box 2 - Humidity
    epd.rect(280, 70, 240, 150, 0)
    epd.text("Humidity", 290, 80, 0)
    epd.text("Living Room", 290, 100, 0)
    epd.text("45 %", 330, 140, 0)
    
    # Box 3 - Status
    epd.rect(540, 70, 240, 150, 0)
    epd.text("System Status", 550, 80, 0)
    epd.text("All OK", 570, 110, 0)
    epd.text("Uptime: 48h", 550, 140, 0)
    
    # Bottom info
    epd.rect(20, 240, 760, 180, 0)
    epd.text("Weather Forecast", 30, 250, 0)
    epd.hline(20, 270, 760, 0)
    epd.text("Today: Sunny, High 25C", 30, 290, 0)
    epd.text("Tomorrow: Partly Cloudy, 23C", 30, 320, 0)
    
    # Battery status (if available)
    try:
        bat = BatteryMonitor()
        voltage = bat.read_voltage()
        epd.text(f"Battery: {voltage:.2f}V", 600, 450, 0)
    except:
        pass
    
    epd.display()
    return epd


def demo_test_pattern():
    """Test pattern for screen alignment"""
    print("\n=== Test Pattern Demo ===")
    epd = EPD_7in5()
    
    epd.fill(1)
    
    # Border
    epd.rect(0, 0, 800, 480, 0)
    
    # Crosshairs
    epd.hline(0, 240, 800, 0)  # Horizontal center
    epd.vline(400, 0, 480, 0)  # Vertical center
    
    # Corner markers
    epd.rect(10, 10, 50, 50, 0)
    epd.rect(740, 10, 50, 50, 0)
    epd.rect(10, 420, 50, 50, 0)
    epd.rect(740, 420, 50, 50, 0)
    
    # Text at corners
    epd.text("TOP LEFT", 15, 70, 0)
    epd.text("TOP RIGHT", 690, 70, 0)
    epd.text("BOTTOM LEFT", 15, 400, 0)
    epd.text("BOTTOM RIGHT", 660, 400, 0)
    
    # Center text
    epd.text("800x480 Resolution", 320, 230, 0)
    epd.text("Test Pattern", 340, 250, 0)
    
    epd.display()
    return epd


def main():
    """Main demo - runs automatically"""
    print("\n" + "="*50)
    print("Seeed Studio 7.5\" ePaper Display")
    print("with ePaper Driver Board")
    print("Resolution: 800x480")
    print("="*50 + "\n")
    
    try:
        # Run Hello World demo
        epd = demo_hello_world()
        print("\nDemo complete! Display will sleep in 5 seconds...")
        time.sleep(5)
        
        # Uncomment to try other demos:
        # epd = demo_dashboard()
        # time.sleep(5)
        
        # epd = demo_test_pattern()
        # time.sleep(5)
        
        # Put display to sleep to save battery
        epd.sleep()
        print("\nAll done!")
        
    except Exception as e:
        print(f"\nError: {e}")
        import sys
        sys.print_exception(e)


# Auto-run on import
if __name__ == "__main__":
    main()
