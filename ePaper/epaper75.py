from machine import Pin, SPI
import time
import framebuf

class EPD:
    def __init__(self):
        self.width = 800
        self.height = 480
        
        # Pin Mapping for Seeed ePaper Driver Board + XIAO ESP32-C3
        self.cs = Pin(3, Pin.OUT, value=1)
        self.dc = Pin(5, Pin.OUT, value=0)
        self.rst = Pin(2, Pin.OUT, value=1)
        self.busy = Pin(4, Pin.IN)
        
        # SPI 0 is the correct hardware SPI for ESP32-C3 external peripherals
        self.spi = SPI(0, baudrate=4000000, polarity=0, phase=0, sck=Pin(8), mosi=Pin(10))
        
        # Allocation of 48KB Framebuffer
        self.buffer = bytearray(self.width * self.height // 8)
        self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_HLSB)

    def _command(self, reg):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([reg]))
        self.cs.value(1)

    def _data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(bytearray(data))
        self.cs.value(1)

    def wait_until_idle(self):
        while self.busy.value() == 1: # 0: idle, 1: busy
            time.sleep_ms(100)

    def reset(self):
        self.rst.value(1)
        time.sleep_ms(200)
        self.rst.value(0)
        time.sleep_ms(2)
        self.rst.value(1)
        time.sleep_ms(200)

    def init(self):
        self.reset()
        self.wait_until_idle()
        
        self._command(0x01) # Power Setting
        self._data([0x07, 0x07, 0x3f, 0x3f])
        
        self._command(0x04) # Power ON
        self.wait_until_idle()
        
        self._command(0x00) # Panel Setting
        self._data(0x1F)    # KW-BF, KWR-AF, BWROTP
        
        self._command(0x61) # Resolution setting
        self._data([0x03, 0x20, 0x01, 0xE0]) # 800x480
        
        self._command(0x15) # Dual SPI mode
        self._data(0x00)
        
        self._command(0x50) # VCOM and Data Interval
        self._data([0x10, 0x07])
        
        self._command(0x60) # TCON setting
        self._data(0x22)

    def display(self):
        # Data Transmission 1 (Old data/Black)
        self._command(0x10)
        self._data([0x00] * (self.width * self.height // 8))
        
        # Data Transmission 2 (New data/Buffer)
        self._command(0x13)
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(self.buffer)
        self.cs.value(1)
        
        self._command(0x12) # Display Refresh
        time.sleep_ms(100)
        self.wait_until_idle()

    def sleep(self):
        self._command(0x02) # Power Off
        self.wait_until_idle()
        self._command(0x07) # Deep Sleep
        self._data(0xA5)
