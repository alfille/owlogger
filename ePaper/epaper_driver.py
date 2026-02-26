"""
MicroPython driver for Seeed Studio 7.5" ePaper Display
Using XIAO ESP32-C3 + Seeed Studio ePaper Driver Board

Hardware Setup:
1. XIAO ESP32-C3 plugged into the ePaper Driver Board socket
2. 7.5" Monochrome ePaper (800x480) connected via 24-pin FPC connector
3. (Optional) LiPo battery connected to JST connector

The ePaper Driver Board provides:
- Automatic pin routing when XIAO is plugged in
- Battery charging circuit with switch
- 3 user buttons
- Easy FPC connector for display

XIAO ESP32-C3 Pin Mapping on Driver Board:
- SPI MOSI: GPIO10 (D10)
- SPI CLK: GPIO8 (D8)  
- CS (Chip Select): GPIO3 (D3)
- DC (Data/Command): GPIO5 (D5)
- RST (Reset): GPIO2 (D2)
- BUSY: GPIO4 (D4)
- Battery ADC: GPIO1 (A0)
- ADC Enable: GPIO6 (D6)

Note: These pins are pre-wired on the driver board!
"""

from machine import Pin, SPI, ADC
import time
import framebuf

class EPD_7in5_V2:
    """
    Driver for 7.5 inch ePaper V2 display (800x480 resolution)
    Optimized for XIAO ESP32-C3 + Seeed ePaper Driver Board
    """
    
    # Display resolution
    WIDTH = 800
    HEIGHT = 480
    
    # Display commands
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
    PLL_CONTROL = 0x30
    TEMPERATURE_SENSOR_COMMAND = 0x40
    TEMPERATURE_SENSOR_CALIBRATION = 0x41
    TEMPERATURE_SENSOR_WRITE = 0x42
    TEMPERATURE_SENSOR_READ = 0x43
    VCOM_AND_DATA_INTERVAL_SETTING = 0x50
    LOW_POWER_DETECTION = 0x51
    TCON_SETTING = 0x60
    TCON_RESOLUTION = 0x61
    SOURCE_AND_GATE_START_SETTING = 0x62
    GET_STATUS = 0x71
    AUTO_MEASURE_VCOM = 0x80
    VCOM_VALUE = 0x81
    VCM_DC_SETTING_REGISTER = 0x82
    PROGRAM_MODE = 0xA0
    ACTIVE_PROGRAM = 0xA1
    READ_OTP_DATA = 0xA2
    
    def __init__(self, use_busy=False):
        """
        Initialize ePaper display with ESP32-C3 driver board pins
        
        Args:
            use_busy: Set to False if BUSY pin is stuck or not connected
        """
        print("="*50)
        print("Initializing 7.5\" ePaper with ESP32-C3")
        if not use_busy:
            print("BUSY PIN DISABLED - Using fixed delays")
        print("="*50)
        
        self.use_busy = use_busy
        
        # Initialize SPI
        # ESP32-C3 uses HSPI (SPI2) with these pins on driver board
        print("Setting up SPI...")
        self.spi = SPI(
            1,  # HSPI bus
            baudrate=4_000_000,  # 4 MHz
            polarity=0,
            phase=0,
            bits=8,
            firstbit=SPI.MSB,
            sck=Pin(8),   # D8 - SCK
            mosi=Pin(10), # D10 - MOSI
            miso=None     # Not used
        )
        print(f"  SPI initialized at 4 MHz")
        
        # Control pins (pre-wired on driver board)
        print("Setting up control pins...")
        self.cs = Pin(3, Pin.OUT, value=1)    # D3 - CS (start high)
        self.dc = Pin(5, Pin.OUT, value=0)    # D5 - DC
        self.rst = Pin(2, Pin.OUT, value=1)   # D2 - RST (start high)
        
        if self.use_busy:
            self.busy = Pin(4, Pin.IN)  # D4 - BUSY (no pull-up)
            print(f"  BUSY pin enabled, initial state: {self.busy.value()}")
        else:
            self.busy = None
            print("  BUSY pin disabled - using timed delays")
        
        print("  Control pins configured")
        
        # Display properties
        self.width = self.WIDTH
        self.height = self.HEIGHT
        
        # Create framebuffer
        print("Allocating framebuffer...")
        buffer_size = self.width * self.height // 8
        print(f"  Buffer size: {buffer_size} bytes ({buffer_size/1024:.1f} KB)")
        
        try:
            self.buffer = bytearray(buffer_size)
            self.framebuf = framebuf.FrameBuffer(
                self.buffer, 
                self.width, 
                self.height, 
                framebuf.MONO_HLSB
            )
            print("  Framebuffer allocated successfully")
        except MemoryError:
            print("  ERROR: Not enough memory for framebuffer!")
            raise
        
        # Initialize the display hardware
        print("\nInitializing display hardware...")
        self.init()
        print("\nDisplay ready!\n")
    
    def _command(self, command):
        """Send command byte to display"""
        self.dc.value(0)  # Command mode
        self.cs.value(0)  # Select
        self.spi.write(bytearray([command]))
        self.cs.value(1)  # Deselect
    
    def _data(self, data):
        """Send data to display"""
        self.dc.value(1)  # Data mode
        self.cs.value(0)  # Select
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)  # Deselect
    
    def _data_batch(self, data):
        """Send large amount of data efficiently"""
        self.dc.value(1)  # Data mode
        self.cs.value(0)  # Select
        self.spi.write(data)
        self.cs.value(1)  # Deselect
    
    def wait_until_idle(self):
        """Wait until display is ready"""
        if not self.use_busy:
            # Fixed delay when BUSY pin not used
            print("Waiting (fixed delay)...", end='')
            time.sleep_ms(2000)  # 2 second delay
            print(" Done")
            return
        
        # Original BUSY pin checking
        print("Waiting for display (BUSY pin check)...", end='')
        
        initial = self.busy.value()
        print(f" Initial BUSY={initial}", end='')
        
        timeout = 400  # 40 seconds
        count = 0
        
        while self.busy.value() == 1:
            time.sleep_ms(100)
            count += 1
            if count % 10 == 0:
                print(".", end='')
            if count >= timeout:
                print(f" TIMEOUT! BUSY stuck at {self.busy.value()}")
                print("\nTIP: Use use_busy=False to disable BUSY checks")
                return
        print(" Ready!")
    
    def reset(self):
        """Perform hardware reset"""
        print("  Hardware reset...")
        self.rst.value(1)
        time.sleep_ms(200)
        self.rst.value(0)
        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(200)
        if self.use_busy and self.busy:
            print(f"    BUSY after reset: {self.busy.value()}")
    
    def init(self):
        """Initialize display with proper settings"""
        self.reset()
        
        # Give display time to wake up
        time.sleep_ms(500)
        
        if not self.use_busy:
            print("  Using timed initialization (no BUSY checks)")
            time.sleep_ms(1000)
        else:
            print(f"  BUSY before init: {self.busy.value()}")
            if self.busy.value() == 1:
                print("  WARNING: BUSY high before init, waiting briefly...")
                time.sleep_ms(1000)
            else:
                self.wait_until_idle()
        
        # Software reset
        print("  Configuring display...")
        
        # Booster soft start
        self._command(self.BOOSTER_SOFT_START)
        self._data(0x17)
        self._data(0x17)
        self._data(0x27)
        self._data(0x17)
        
        # Power setting
        self._command(self.POWER_SETTING)
        self._data(0x07)
        self._data(0x07)
        self._data(0x3F)
        self._data(0x3F)
        
        # Power on
        self._command(self.POWER_ON)
        time.sleep_ms(100)
        
        # Wait for power-on
        if not self.use_busy:
            time.sleep_ms(2000)  # Fixed delay
        else:
            time.sleep_ms(1000)
            print(f"  BUSY after power on: {self.busy.value()}")
            if self.busy.value() == 0:
                self.wait_until_idle()
            else:
                print("  Skipping BUSY wait")
                time.sleep_ms(2000)
        
        # Panel setting - KW mode
        self._command(self.PANEL_SETTING)
        self._data(0x1F)
        
        # PLL control
        self._command(self.PLL_CONTROL)
        self._data(0x06)
        
        # Resolution setting
        self._command(self.TCON_RESOLUTION)
        self._data(0x03)
        self._data(0x20)
        self._data(0x01)
        self._data(0xE0)
        
        # Dual SPI
        self._command(0x15)
        self._data(0x00)
        
        # VCOM and data interval
        self._command(self.VCOM_AND_DATA_INTERVAL_SETTING)
        self._data(0x10)
        self._data(0x07)
        
        # TCON setting
        self._command(self.TCON_SETTING)
        self._data(0x22)
        
        print("  Display configured!")
    
    def diagnose(self):
        """Run diagnostic checks"""
        print("\n" + "="*50)
        print("DIAGNOSTIC MODE")
        print("="*50)
        
        print("\n1. Pin States:")
        print(f"   CS:   {self.cs.value()} (should be 1)")
        print(f"   DC:   {self.dc.value()}")
        print(f"   RST:  {self.rst.value()} (should be 1)")
        if self.use_busy and self.busy:
            print(f"   BUSY: {self.busy.value()}")
        else:
            print(f"   BUSY: Disabled")
        
        if self.use_busy and self.busy:
            print("\n2. Testing Reset...")
            self.rst.value(0)
            time.sleep_ms(100)
            print(f"   BUSY during reset: {self.busy.value()}")
            self.rst.value(1)
            time.sleep_ms(100)
            print(f"   BUSY after reset: {self.busy.value()}")
        
        print("\n3. Testing SPI...")
        try:
            self.cs.value(0)
            self.spi.write(b'\x00')
            self.cs.value(1)
            print("   SPI write OK")
        except Exception as e:
            print(f"   SPI ERROR: {e}")
        
        print("\n4. Configuration:")
        print(f"   BUSY checks: {'Enabled' if self.use_busy else 'Disabled (using fixed delays)'}")
        
        print("="*50 + "\n")
    
    def clear(self, color=0xFF):
        """
        Clear the display
        color: 0xFF (white) or 0x00 (black)
        """
        print(f"Clearing display to {'white' if color == 0xFF else 'black'}...")
        
        # Clear both image buffers
        self._command(self.DATA_START_TRANSMISSION_1)
        for _ in range(self.width * self.height // 8):
            self._data(color)
        
        self._command(self.DATA_START_TRANSMISSION_2)
        for _ in range(self.width * self.height // 8):
            self._data(color)
        
        self._command(self.DISPLAY_REFRESH)
        time.sleep_ms(100)
        self.wait_until_idle()
        print("Display cleared!")
    
    def display(self):
        """Update display with framebuffer content"""
        print("Sending image data...")
        
        # Send old image (for clean refresh)
        self._command(self.DATA_START_TRANSMISSION_1)
        white_line = bytearray([0xFF] * 100)
        for _ in range((self.width * self.height // 8) // 100):
            self._data_batch(white_line)
        
        # Send new image
        print("  Transferring framebuffer...")
        self._command(self.DATA_START_TRANSMISSION_2)
        self._data_batch(self.buffer)
        
        # Refresh display
        print("  Refreshing display...")
        self._command(self.DISPLAY_REFRESH)
        time.sleep_ms(100)
        self.wait_until_idle()
        print("Display updated successfully!")
    
    def sleep(self):
        """Enter deep sleep mode (saves power)"""
        print("Entering sleep mode...")
        self._command(self.POWER_OFF)
        self.wait_until_idle()
        self._command(self.DEEP_SLEEP)
        self._data(0xA5)
        time.sleep_ms(200)
        print("Display sleeping")
    
    # Drawing API - delegates to framebuffer
    def fill(self, color):
        """Fill display (0=black, 1=white)"""
        self.framebuf.fill(color)
    
    def pixel(self, x, y, color):
        """Set pixel"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.framebuf.pixel(x, y, color)
    
    def hline(self, x, y, w, color):
        """Horizontal line"""
        self.framebuf.hline(x, y, w, color)
    
    def vline(self, x, y, h, color):
        """Vertical line"""
        self.framebuf.vline(x, y, h, color)
    
    def line(self, x1, y1, x2, y2, color):
        """Draw line"""
        self.framebuf.line(x1, y1, x2, y2, color)
    
    def rect(self, x, y, w, h, color, fill=False):
        """Draw rectangle"""
        if fill:
            self.framebuf.fill_rect(x, y, w, h, color)
        else:
            self.framebuf.rect(x, y, w, h, color)
    
    def text(self, s, x, y, color=0):
        """Draw text (8x8 font)"""
        self.framebuf.text(s, x, y, color)


class BatteryMonitor:
    """Monitor battery on ESP32-C3 driver board"""
    
    def __init__(self):
        print("Initializing battery monitor...")
        # ADC enable pin
        self.adc_enable = Pin(6, Pin.OUT)
        self.adc_enable.value(1)  # Enable
        
        # Battery voltage pin
        self.adc = ADC(Pin(1))
        self.adc.atten(ADC.ATTN_11DB)  # 0-3.3V range
        self.adc.width(ADC.WIDTH_12BIT)  # 12-bit resolution
        print("  Battery monitor ready")
    
    def read_voltage(self):
        """Read battery voltage"""
        # Read ADC value (0-4095)
        raw = self.adc.read()
        # Convert to voltage (driver board has voltage divider)
        voltage = (raw / 4095.0) * 3.3 * 2.0  # 2:1 divider
        return voltage
    
    def get_percentage(self):
        """Estimate battery percentage"""
        v = self.read_voltage()
        # LiPo voltage: 4.2V (full) to 3.0V (empty)
        if v >= 4.2:
            return 100
        elif v <= 3.0:
            return 0
        else:
            return int(((v - 3.0) / 1.2) * 100)


# Demo functions
def demo_diagnostic(use_busy=False):
    """Run diagnostic check"""
    print("\n" + "="*50)
    print("DEMO: Diagnostic Check")
    print("="*50 + "\n")
    
    try:
        epd = EPD_7in5_V2(use_busy=use_busy)
        epd.diagnose()
        return epd
    except Exception as e:
        print(f"Error during init: {e}")
        import sys
        sys.print_exception(e)


def demo_hello(use_busy=False):
    """Simple hello world"""
    print("\n" + "="*50)
    print("DEMO: Hello World")
    print("="*50 + "\n")
    
    epd = EPD_7in5_V2(use_busy=use_busy)
    epd.clear()
    
    epd.fill(1)
    epd.text("Seeed Studio ePaper", 250, 100, 0)
    epd.text("7.5 inch - 800x480", 250, 120, 0)
    epd.text("XIAO ESP32-C3", 250, 140, 0)
    epd.text("with Driver Board", 250, 160, 0)
    
    # Border
    epd.rect(10, 10, 780, 460, 0)
    epd.rect(15, 15, 770, 450, 0)
    
    epd.display()
    return epd


def demo_dashboard(use_busy=False):
    """Dashboard with battery info"""
    print("\n" + "="*50)
    print("DEMO: Dashboard")
    print("="*50 + "\n")
    
    epd = EPD_7in5_V2(use_busy=use_busy)
    bat = BatteryMonitor()
    
    epd.fill(1)
    
    # Title
    epd.rect(0, 0, 800, 60, 0, fill=True)
    epd.text("SYSTEM DASHBOARD", 280, 25, 1)
    
    # Info boxes
    epd.rect(20, 80, 360, 160, 0)
    epd.text("TEMPERATURE", 30, 90, 0)
    epd.text("Living Room: 22.5 C", 30, 120, 0)
    epd.text("Bedroom: 21.0 C", 30, 140, 0)
    epd.text("Kitchen: 23.5 C", 30, 160, 0)
    
    epd.rect(420, 80, 360, 160, 0)
    epd.text("HUMIDITY", 430, 90, 0)
    epd.text("Living Room: 45%", 430, 120, 0)
    epd.text("Bedroom: 50%", 430, 140, 0)
    epd.text("Kitchen: 55%", 430, 160, 0)
    
    # Status
    epd.rect(20, 260, 760, 140, 0)
    epd.text("SYSTEM STATUS", 30, 270, 0)
    epd.hline(20, 290, 760, 0)
    epd.text("ESP32-C3: OK", 30, 310, 0)
    epd.text("WiFi: Connected", 30, 330, 0)
    epd.text("Uptime: 24h 35m", 30, 350, 0)
    
    # Battery info
    try:
        voltage = bat.read_voltage()
        percent = bat.get_percentage()
        epd.text(f"Battery: {voltage:.2f}V ({percent}%)", 500, 310, 0)
    except:
        epd.text("Battery: N/A", 500, 310, 0)
    
    # Time/Date (placeholder)
    import time
    t = time.localtime()
    epd.text(f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}", 650, 440, 0)
    
    epd.display()
    return epd


def demo_test_pattern(use_busy=False):
    """Test pattern"""
    print("\n" + "="*50)
    print("DEMO: Test Pattern")
    print("="*50 + "\n")
    
    epd = EPD_7in5_V2(use_busy=use_busy)
    
    epd.fill(1)
    
    # Grid
    for x in range(0, 801, 100):
        epd.vline(x, 0, 480, 0)
    for y in range(0, 481, 80):
        epd.hline(0, y, 800, 0)
    
    # Center crosshair
    epd.hline(0, 240, 800, 0)
    epd.vline(400, 0, 480, 0)
    
    # Corners
    epd.rect(10, 10, 80, 60, 0, fill=True)
    epd.rect(710, 10, 80, 60, 0, fill=True)
    epd.rect(10, 410, 80, 60, 0, fill=True)
    epd.rect(710, 410, 80, 60, 0, fill=True)
    
    epd.text("800x480 Test Pattern", 310, 230, 0)
    
    epd.display()
    return epd


def main():
    """Main demo"""
    print("\n" + "#"*50)
    print("# Seeed Studio 7.5\" ePaper Display")
    print("# XIAO ESP32-C3 + Driver Board")
    print("# MicroPython Demo")
    print("#"*50 + "\n")
    
    print("Choose a demo:")
    print("1. Diagnostic check (recommended if having issues)")
    print("2. Simple test (no BUSY checks)")
    print("3. Normal demo\n")
    
    # Auto-run diagnostic if stuck
    print("Running diagnostic first...\n")
    demo_diagnostic()
    
    print("\n\nNow trying simple test...")
    demo_simple_test()
    
    # Uncomment to try normal demo:
    # try:
    #     epd = demo_hello()
    #     print("\nWaiting 5 seconds...")
    #     time.sleep(5)
    #     epd.sleep()
    #     print("\n✓ Demo complete!\n")
    # except Exception as e:
    #     print(f"\n✗ Error: {e}\n")
    #     import sys
    #     sys.print_exception(e)


if __name__ == "__main__":
    main()
