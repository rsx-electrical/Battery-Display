from machine import Pin, SPI
import time

# Your schematic pins
BUSY = Pin(13, Pin.IN, Pin.PULL_UP)   # Display pin 9 BUSY_N
RST  = Pin(11, Pin.OUT, value=1)      # Display pin 10 RST_N
DC   = Pin(12, Pin.OUT, value=1)      # Display pin 11 D/C
CS   = Pin(17, Pin.OUT, value=1)      # Display pin 12 CSB
EN   = Pin(6, Pin.OUT, value=1)       # Harmless if Q3 is shorted
LED  = Pin(25, Pin.OUT, value=0)      # Pico onboard LED

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
            raise RuntimeError("BUSY timeout")
        time.sleep_ms(10)


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
    reset()

    # Minimal init sequence from the Pervasive 206_KS_0E driver.
    # This uses placeholder PSR bytes instead of reading OTP.
    cmd_data(0x00, bytes([0x0E]))
    wait_busy()

    cmd_data(0xE5, bytes([25]))       # temperature = 25 C
    cmd_data(0xE0, bytes([0x02]))     # activate temperature

    # Placeholder PSR bytes.
    cmd_data(0x00, bytes([0xCF, 0x82]))

    # Image data: all black
    black = bytes([0x00]) * FRAME_SIZE

    cmd(0x10)
    data(black)

    fill_cmd(0x13, 0x00, FRAME_SIZE)

    wait_busy()

    cmd(0x04)                         # power on
    wait_busy(30000)

    cmd(0x12)                         # display refresh
    wait_busy(60000)

    cmd(0x02)                         # power off DCDC
    wait_busy(30000)


update_black_minimal()

# Only idle blink
while True:
    LED.value(1)
    time.sleep_ms(500)
    LED.value(0)
    time.sleep_ms(500)