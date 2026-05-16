from machine import Pin, SPI
import time

# Pico onboard LED
led = Pin("LED", Pin.OUT)
led.value(1)   # LED stays ON as basic Pico/code-running test

# GPIO numbers from your schematic
DISPLAY_EN = Pin(6, Pin.OUT)

RST  = Pin(11, Pin.OUT)
DC   = Pin(12, Pin.OUT)
BUSY = Pin(13, Pin.IN)

CS   = Pin(17, Pin.OUT)
SCK  = Pin(18)
MOSI = Pin(19)

spi = SPI(
    0,
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    sck=SCK,
    mosi=MOSI,
    miso=None
)

# Turn on display power
DISPLAY_EN.value(1)   # try HIGH first
time.sleep(1)

print("Pico LED ON")
print("Display enable HIGH")
print("BUSY =", BUSY.value())

# Reset pulse
RST.value(1)
time.sleep(0.2)
RST.value(0)
time.sleep(0.2)
RST.value(1)
time.sleep(0.5)

print("Reset toggled")
print("BUSY =", BUSY.value())

while True:
    led.value(1)  # keep LED on

    CS.value(0)
    DC.value(0)       # command mode
    spi.write(b'\x00\xFF\xAA\x55')
    CS.value(1)

    time.sleep(0.5)

    CS.value(0)
    DC.value(1)       # data mode
    spi.write(b'\xFF\x00\x55\xAA')
    CS.value(1)

    print("Sent SPI bytes, BUSY =", BUSY.value())
    time.sleep(1)