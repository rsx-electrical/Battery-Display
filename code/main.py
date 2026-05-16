from machine import Pin, SPI
import time

# Your schematic pins
BUSY = Pin(13, Pin.IN, Pin.PULL_UP)   # Display pin 9 BUSY_N
RST  = Pin(11, Pin.OUT, value=1)      # Display pin 10 RST_N
DC   = Pin(12, Pin.OUT, value=1)      # Display pin 11 D/C
CS   = Pin(17, Pin.OUT, value=1)      # Display pin 12 CSB
LED  = Pin(25, Pin.OUT)
EN   = Pin(6, Pin.OUT, value=1)       # Harmless if Q3 is shorted

spi = SPI(
    0,
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    bits=8,
    firstbit=SPI.MSB,
    sck=Pin(18),      # Display pin 13 SCL
    mosi=Pin(19),     # Display pin 14 SDA
)

WIDTH = 248
HEIGHT = 128
FRAME_SIZE = WIDTH * HEIGHT // 8


def blink(n):
    for _ in range(n):
        LED.value(1)
        time.sleep_ms(120)
        LED.value(0)
        time.sleep_ms(120)
    time.sleep_ms(500)


def die(code):
    while True:
        blink(code)
        time.sleep_ms(1000)


def reset():
    CS.value(1)
    DC.value(1)

    RST.value(1)
    time.sleep_ms(10)
    RST.value(0)
    time.sleep_ms(10)
    RST.value(1)
    time.sleep_ms(50)


def wait_busy(timeout_ms=15000):
    # BUSY_N: low = busy, high = ready
    start = time.ticks_ms()
    while BUSY.value() == 0:
        if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
            return False
        time.sleep_ms(10)
    return True


def cmd(c):
    DC.value(0)
    CS.value(0)
    spi.write(bytes([c]))
    CS.value(1)


def data(b):
    DC.value(1)
    CS.value(0)
    if isinstance(b, int):
        spi.write(bytes([b]))
    else:
        # chunk large frame writes
        for i in range(0, len(b), 256):
            spi.write(b[i:i + 256])
    CS.value(1)


def cmd_data(c, b):
    cmd(c)
    data(b)


def fill_cmd(c, value, count):
    cmd(c)
    DC.value(1)
    CS.value(0)
    block = bytes([value]) * 256
    for _ in range(count // 256):
        spi.write(block)
    rem = count % 256
    if rem:
        spi.write(bytes([value]) * rem)
    CS.value(1)


def update_black_minimal():
    blink(1)
    reset()

    # Minimal init sequence from the Pervasive driver for 206_KS_0E.
    # NOTE: Real production code should read PSR from OTP.
    # These default PSR bytes may or may not match your exact panel lot,
    # but this is a useful quick sanity test.
    cmd_data(0x00, bytes([0x0E]))     # soft reset / panel setting
    if not wait_busy():
        die(2)

    cmd_data(0xE5, bytes([25]))       # temperature = 25 C
    cmd_data(0xE0, bytes([0x02]))     # activate temperature

    # Placeholder PSR. If this does not work, the next version should add OTP read.
    cmd_data(0x00, bytes([0xCF, 0x82]))

    blink(3)

    # Image data: all black
    black = bytes([0x00]) * FRAME_SIZE

    cmd(0x10)
    data(black)

    fill_cmd(0x13, 0x00, FRAME_SIZE)

    if not wait_busy():
        die(4)

    cmd(0x04)                         # power on
    if not wait_busy(30000):
        die(5)

    cmd(0x12)                         # display refresh
    if not wait_busy(60000):
        die(6)

    cmd(0x02)                         # power off DCDC
    if not wait_busy(30000):
        die(7)

    blink(8)


update_black_minimal()

while True:
    blink(1)
    time.sleep_ms(1000)