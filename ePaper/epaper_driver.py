"""
MicroPython driver for Seeed Studio 7.5" ePaper Display
Hardware: XIAO ESP32-C3 + 7.5" Monochrome ePaper (800x480)
Display Controller: Likely based on Waveshare/Good Display controller

Pin Configuration for XIAO 7.5" ePaper Panel:
- CS (Chip Select): GPIO3
- DC (Data/Command): GPIO5
- RST (Reset): GPIO2
- BUSY: GPIO4
- CLK (SPI Clock): GPIO8
- MOSI (SPI Data): GPIO10
"""

from machine import Pin, SPI
import time
import framebuf

class EPD_7in5:
    """Driver for 7.5 inch ePaper display (800x480 resolution)"""
    
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
    VCOM_AND_DATA_INTERVAL_SETTING = 0x50
    RESOLUTION_SETTING = 0x61
    
    def __init__(self):
        """Initialize the ePaper display"""
        # Setup SPI
        self.spi = SPI(1, baudrate=4000000, polarity=0, phase=0,
                      sck=Pin(8), mosi=Pin(10), miso=None)
        
        # Setup control pins
        self.cs = Pin(3, Pin.OUT)
        self.dc = Pin(5, Pin.OUT)
        self.rst = Pin(2, Pin.OUT)
        self.busy = Pin(4, Pin.IN)
        
        # Create framebuffer (1 bit per pixel, monochrome)
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.buffer = bytearray(self.width * self.height // 8)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, 
                                            self.height, framebuf.MONO_HLSB)
        
        # Initialize display
        self.init()
    
    def _command(self, command):
        """Send command to display"""
        self.dc.value(0)  # Command mode
        self.cs.value(0)
        self.spi.write(bytearray([command]))
        self.cs.value(1)
    
    def _data(self, data):
        """Send data to display"""
        self.dc.value(1)  # Data mode
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)
    
    def wait_until_idle(self):
        """Wait until the display is ready"""
        print("Waiting for display...")
        while self.busy.value() == 1:  # HIGH = busy
            time.sleep_ms(10)
        print("Display ready")
    
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
        self._command(self.POWER_SETTING)
        self._data(0x07)
        self._data(0x07)
        self._data(0x3f)
        self._data(0x3f)
        
        self._command(self.POWER_ON)
        time.sleep_ms(100)
        self.wait_until_idle()
        
        self._command(self.PANEL_SETTING)
        self._data(0x1f)  # KW-3f, KWR-2F, BWROTP 0f, BWOTP 1f
        
        self._command(self.RESOLUTION_SETTING)
        self._data(0x03)  # 800x480
        self._data(0x20)
        self._data(0x01)
        self._data(0xE0)
        
        self._command(self.VCOM_AND_DATA_INTERVAL_SETTING)
        self._data(0x10)
        self._data(0x07)
        
        print("ePaper display initialized")
    
    def clear(self, color=0xFF):
        """Clear the display (0xFF=white, 0x00=black)"""
        print("Clearing display...")
        
        # Send white to both image buffers
        self._command(self.DATA_START_TRANSMISSION_1)
        for _ in range(self.width * self.height // 8):
            self._data(color)
        
        self._command(self.DATA_START_TRANSMISSION_2)
        for _ in range(self.width * self.height // 8):
            self._data(color)
        
        self._command(self.DISPLAY_REFRESH)
        time.sleep_ms(100)
        self.wait_until_idle()
        print("Display cleared")
    
    def display(self):
        """Update the display with framebuffer contents"""
        print("Updating display...")
        
        # Send old image data (for proper refresh)
        self._command(self.DATA_START_TRANSMISSION_1)
        for _ in range(self.width * self.height // 8):
            self._data(0xFF)
        
        # Send new image data
        self._command(self.DATA_START_TRANSMISSION_2)
        self._data(self.buffer)
        
        # Refresh display
        self._command(self.DISPLAY_REFRESH)
        time.sleep_ms(100)
        self.wait_until_idle()
        print("Display updated")
    
    def sleep(self):
        """Put display into deep sleep mode"""
        self._command(self.DEEP_SLEEP)
        self._data(0xA5)
        time.sleep_ms(2000)
    
    # Drawing methods (delegate to framebuffer)
    def fill(self, color):
        """Fill entire display with color (0=black, 1=white)"""
        self.framebuf.fill(color)
    
    def pixel(self, x, y, color):
        """Set a single pixel"""
        self.framebuf.pixel(x, y, color)
    
    def hline(self, x, y, width, color):
        """Draw horizontal line"""
        self.framebuf.hline(x, y, width, color)
    
    def vline(self, x, y, height, color):
        """Draw vertical line"""
        self.framebuf.vline(x, y, height, color)
    
    def line(self, x1, y1, x2, y2, color):
        """Draw line"""
        self.framebuf.line(x1, y1, x2, y2, color)
    
    def rect(self, x, y, width, height, color, fill=False):
        """Draw rectangle"""
        if fill:
            self.framebuf.fill_rect(x, y, width, height, color)
        else:
            self.framebuf.rect(x, y, width, height, color)
    
    def text(self, string, x, y, color=0):
        """Draw text (8x8 font)"""
        self.framebuf.text(string, x, y, color)
    
    def circle(self, x, y, radius, color):
        """Draw circle (simple implementation)"""
        for angle in range(0, 360, 5):
            x_pos = int(x + radius * __import__('math').cos(__import__('math').radians(angle)))
            y_pos = int(y + radius * __import__('math').sin(__import__('math').radians(angle)))
            if 0 <= x_pos < self.width and 0 <= y_pos < self.height:
                self.pixel(x_pos, y_pos, color)


# Example usage functions
def demo_basic():
    """Basic demo - Hello World"""
    print("=== Basic Demo ===")
    epd = EPD_7in5()
    
    # Clear display
    epd.clear()
    
    # Draw some text
    epd.fill(1)  # White background
    epd.text("Hello World!", 50, 50, 0)
    epd.text("Seeed Studio", 50, 70, 0)
    epd.text("7.5 inch ePaper", 50, 90, 0)
    epd.text("800x480 Resolution", 50, 110, 0)
    
    # Draw some shapes
    epd.rect(200, 50, 150, 100, 0)
    epd.rect(202, 52, 146, 96, 0, fill=True)
    
    # Update display
    epd.display()
    
    print("Demo complete")
    return epd


def demo_dashboard():
    """Dashboard demo with sections"""
    print("=== Dashboard Demo ===")
    epd = EPD_7in5()
    
    epd.fill(1)  # White background
    
    # Title
    epd.text("HOME DASHBOARD", 300, 10, 0)
    epd.hline(0, 30, 800, 0)
    
    # Left column - Temperature
    epd.rect(10, 50, 250, 150, 0)
    epd.text("Temperature", 20, 60, 0)
    epd.text("Living Room", 20, 80, 0)
    epd.text("22.5 C", 50, 120, 0)
    
    # Middle column - Humidity  
    epd.rect(270, 50, 250, 150, 0)
    epd.text("Humidity", 280, 60, 0)
    epd.text("Living Room", 280, 80, 0)
    epd.text("45%", 320, 120, 0)
    
    # Right column - Status
    epd.rect(530, 50, 250, 150, 0)
    epd.text("System", 540, 60, 0)
    epd.text("Status: OK", 540, 80, 0)
    epd.text("Uptime: 24h", 540, 100, 0)
    
    # Bottom section
    epd.rect(10, 220, 780, 100, 0)
    epd.text("Weather Forecast", 20, 230, 0)
    epd.text("Sunny, 25C", 20, 250, 0)
    
    epd.display()
    print("Dashboard complete")
    return epd


def demo_graphics():
    """Graphics demo"""
    print("=== Graphics Demo ===")
    epd = EPD_7in5()
    
    epd.fill(1)
    
    # Draw grid
    for x in range(0, 800, 50):
        epd.vline(x, 0, 480, 0)
    for y in range(0, 480, 50):
        epd.hline(0, y, 800, 0)
    
    # Draw some patterns
    for i in range(10):
        epd.rect(50 + i*30, 100 + i*10, 100, 100, 0)
    
    epd.text("Graphics Test", 300, 10, 0)
    
    epd.display()
    print("Graphics demo complete")
    return epd


def main():
    """Main demo function"""
    print("Seeed Studio 7.5\" ePaper Display Demo")
    print("Resolution: 800x480")
    print("=" * 40)
    
    try:
        # Run basic demo
        epd = demo_basic()
        time.sleep(3)
        
        # Uncomment to run other demos:
        # epd = demo_dashboard()
        # time.sleep(3)
        
        # epd = demo_graphics()
        
        # Put display to sleep to save power
        print("Putting display to sleep...")
        epd.sleep()
        
    except Exception as e:
        print(f"Error: {e}")
        import sys
        sys.print_exception(e)


if __name__ == "__main__":
    main()
