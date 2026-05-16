from machine import Pin, SPI
import framebuf
import time

# -----------------------------
# Pico onboard LED
# -----------------------------
led = Pin("LED", Pin.OUT)
led.value(1)

# -----------------------------
# Your schematic pins
# -----------------------------
DISPLAY_EN = Pin(6, Pin.OUT)

RST  = Pin(11, Pin.OUT)
DC   = Pin(12, Pin.OUT)
BUSY = Pin(13, Pin.IN)

CS   = Pin(17, Pin.OUT)
SCK  = Pin(18)
MOSI = Pin(19)

spi = SPI(
    0,
    baudrate=2_000_000,
    polarity=0,
    phase=0,
    sck=SCK,
    mosi=MOSI,
    miso=None
)

# -----------------------------
# Display size
# Change these if your panel is different
# Common 2.13 inch e-paper: 250 x 122
# -----------------------------
WIDTH  = 250
HEIGHT = 122

# For 1-bit display: 1 bit per pixel
buf = bytearray((WIDTH * HEIGHT) // 8)
fb = framebuf.FrameBuffer(buf, WIDTH, HEIGHT, framebuf.MONO_HLSB)


def digital_write(pin, value):
    pin.value(value)


def send_command(cmd):
    DC.value(0)
    CS.value(0)
    spi.write(bytearray([cmd]))
    CS.value(1)


def send_data(data):
    DC.value(1)
    CS.value(0)

    if isinstance(data, int):
        spi.write(bytearray([data]))
    else:
        spi.write(bytearray(data))

    CS.value(1)


def reset_display():
    RST.value(1)
    time.sleep_ms(200)
    RST.value(0)
    time.sleep_ms(10)
    RST.value(1)
    time.sleep_ms(200)


def wait_until_idle():
    print("Waiting for BUSY...")
    timeout = 5000

    # Many e-paper displays are busy while BUSY = 1
    while BUSY.value() == 1 and timeout > 0:
        time.sleep_ms(10)
        timeout -= 10

    print("BUSY =", BUSY.value())


def init_display():
    reset_display()

    # Software reset
    send_command(0x12)
    time.sleep_ms(100)
    wait_until_idle()

    # Driver output control
    send_command(0x01)
    send_data((HEIGHT - 1) & 0xFF)
    send_data(((HEIGHT - 1) >> 8) & 0xFF)
    send_data(0x00)

    # Data entry mode
    send_command(0x11)
    send_data(0x03)

    # Set RAM X address range
    send_command(0x44)
    send_data(0x00)
    send_data((WIDTH // 8) - 1)

    # Set RAM Y address range
    send_command(0x45)
    send_data(0x00)
    send_data(0x00)
    send_data((HEIGHT - 1) & 0xFF)
    send_data(((HEIGHT - 1) >> 8) & 0xFF)

    # Border waveform
    send_command(0x3C)
    send_data(0x05)

    # Internal temperature sensor
    send_command(0x18)
    send_data(0x80)

    # Set RAM X/Y pointer
    send_command(0x4E)
    send_data(0x00)

    send_command(0x4F)
    send_data(0x00)
    send_data(0x00)

    wait_until_idle()


def display_frame():
    # Set RAM pointer to beginning
    send_command(0x4E)
    send_data(0x00)

    send_command(0x4F)
    send_data(0x00)
    send_data(0x00)

    # Write black/white RAM
    send_command(0x24)
    send_data(buf)

    # Refresh display
    send_command(0x22)
    send_data(0xF7)
    send_command(0x20)

    wait_until_idle()


def clear_screen():
    fb.fill(1)  # white
    display_frame()


def draw_test_pattern():
    fb.fill(1)  # white background

    # black border
    fb.rect(0, 0, WIDTH, HEIGHT, 0)

    # text
    fb.text("PICO OK", 10, 10, 0)
    fb.text("DISPLAY TEST", 10, 30, 0)

    # black boxes
    fb.fill_rect(10, 55, 40, 30, 0)
    fb.fill_rect(70, 55, 40, 30, 0)
    fb.fill_rect(130, 55, 40, 30, 0)

    # lines
    fb.hline(10, 100, 200, 0)
    fb.vline(220, 10, 90, 0)

    display_frame()


# -----------------------------
# Main
# -----------------------------

# Try HIGH first for display enable
DISPLAY_EN.value(1)
time.sleep_ms(500)

print("Pico LED ON")
print("Display enabled")
print("BUSY initial =", BUSY.value())

init_display()
clear_screen()
time.sleep(1)
draw_test_pattern()

print("Done. Display should show border/text/pattern.")

while True:
    led.value(1)
    time.sleep(1)