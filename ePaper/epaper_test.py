import epaper75
import time

def run_demo():
    print("Initializing Display...")
    display = epaper75.EPD()
    display.init()
    
    # 1. Clear buffer (White)
    print("Drawing to buffer...")
    display.fb.fill(1) 
    
    # 2. Draw Graphics
    # Main Border
    display.fb.rect(10, 10, 780, 460, 0) 
    # Header area
    display.fb.fill_rect(10, 10, 780, 60, 0)
    display.fb.text("XIAO ESP32-C3 EPAPER SYSTEM", 280, 35, 1)
    
    # Text Data
    display.fb.text("Device Status: ONLINE", 30, 100, 0)
    display.fb.text("Display Type: 7.5 Inch Monochrome", 30, 120, 0)
    display.fb.text("Resolution: 800x480", 30, 140, 0)
    
    # Simple Progress Bar Example
    display.fb.text("Storage Usage:", 30, 200, 0)
    display.fb.rect(30, 215, 200, 20, 0)
    display.fb.fill_rect(33, 218, 150, 14, 0) # 75% full
    
    # 3. Push to screen
    print("Updating Screen (this takes ~5 seconds)...")
    display.display()
    
    print("Done! Putting display to sleep.")
    display.sleep()

if __name__ == "__main__":
    run_demo()
