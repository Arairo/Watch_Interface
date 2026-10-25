# ---------------------------------------------------------------
#  calibrate.py - find the TOUCH_* numbers for config.py
#
#  Run it from Thonny (open the file, press Run) while the board
#  is plugged in. Tap each red cross. The numbers to paste into
#  config.py are printed in the Shell at the end.
# ---------------------------------------------------------------
import time
from machine import Pin, SPI, SoftSPI
import config as C
from ili9341 import ILI9341, color565
from xpt2046 import XPT2046

spi = SPI(C.TFT_SPI_ID, baudrate=C.TFT_BAUD, sck=Pin(C.TFT_SCK),
          mosi=Pin(C.TFT_MOSI), miso=Pin(C.TFT_MISO))
tft = ILI9341(spi, C.TFT_CS, C.TFT_DC, C.TFT_RST,
              C.TFT_WIDTH, C.TFT_HEIGHT, C.TFT_MADCTL)
Pin(C.TFT_LED, Pin.OUT).value(1)
tspi = SoftSPI(baudrate=1_000_000, sck=Pin(C.TOUCH_SCK),
               mosi=Pin(C.TOUCH_MOSI), miso=Pin(C.TOUCH_MISO))
touch = XPT2046(tspi, C.TOUCH_CS, C.TOUCH_IRQ, swap_xy=C.TOUCH_SWAP_XY)

RED = color565(255, 0, 0)
W, H = C.TFT_WIDTH, C.TFT_HEIGHT
M = 20  # crosses are drawn 20 px in from the edges


def cross(x, y, col):
    tft.fill_rect(x - 10, y, 21, 1, col)
    tft.fill_rect(x, y - 10, 1, 21, col)


def wait_tap():
    while touch.raw() is None:
        time.sleep_ms(20)
    samples = []
    while True:
        r = touch.raw()
        if r is None:
            break
        samples.append(r)
        time.sleep_ms(20)
    while touch.is_touched():
        time.sleep_ms(20)
    if not samples:
        return wait_tap()
    xs = sorted(s[0] for s in samples)
    ys = sorted(s[1] for s in samples)
    rx, ry = xs[len(xs) // 2], ys[len(ys) // 2]
    if C.TOUCH_SWAP_XY:
        rx, ry = ry, rx
    return rx, ry


points = [(M, M), (W - M, M), (W - M, H - M), (M, H - M)]
raw = []
for (x, y) in points:
    tft.fill(0)
    tft.center_text("Tap the red cross", H // 2 - 4, 0xFFFF, 0, 1)
    cross(x, y, RED)
    r = wait_tap()
    print("screen", (x, y), "-> raw", r)
    raw.append(r)

# raw values at the cross positions, extrapolated to the screen edges
left = (raw[0][0] + raw[3][0]) / 2
right = (raw[1][0] + raw[2][0]) / 2
top = (raw[0][1] + raw[1][1]) / 2
bottom = (raw[2][1] + raw[3][1]) / 2
sx = (right - left) / (W - 2 * M)
sy = (bottom - top) / (H - 2 * M)
x_at_0, x_at_w = left - sx * M, right + sx * M
y_at_0, y_at_h = top - sy * M, bottom + sy * M

inv_x = x_at_0 > x_at_w
inv_y = y_at_0 > y_at_h
print()
print("---- paste into config.py ----")
print("TOUCH_X_MIN = %d" % min(x_at_0, x_at_w))
print("TOUCH_X_MAX = %d" % max(x_at_0, x_at_w))
print("TOUCH_Y_MIN = %d" % min(y_at_0, y_at_h))
print("TOUCH_Y_MAX = %d" % max(y_at_0, y_at_h))
print("TOUCH_SWAP_XY  = %s" % C.TOUCH_SWAP_XY)
print("TOUCH_INVERT_X = %s" % inv_x)
print("TOUCH_INVERT_Y = %s" % inv_y)

tft.fill(0)
tft.center_text("Done! See the Shell.", H // 2 - 8, 0xFFFF, 0, 2)
