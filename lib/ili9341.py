# ---------------------------------------------------------------
#  ili9341.py - small, low-RAM MicroPython driver for ILI9341
#  Draws straight to the panel (no full-screen framebuffer), so it
#  runs on a plain ESP32 without PSRAM.
# ---------------------------------------------------------------
import time
import framebuf
from machine import Pin


def color565(r, g, b):
    """Convert 8-bit R, G, B to a 16-bit RGB565 colour."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class ILI9341:
    def __init__(self, spi, cs, dc, rst, width=320, height=240, madctl=0x28):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.dc = Pin(dc, Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=1)
        self.width = width
        self.height = height
        self._madctl = madctl
        self._glyph = bytearray(8)  # 8x8 mono buffer for one character
        self._glyph_fb = framebuf.FrameBuffer(self._glyph, 8, 8, framebuf.MONO_HLSB)
        self.reset()
        self.init()

    # ---------- low level ----------
    def _cmd(self, c, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytes([c]))
        if data is not None:
            self.dc(1)
            self.spi.write(data)
        self.cs(1)

    def reset(self):
        self.rst(0)
        time.sleep_ms(50)
        self.rst(1)
        time.sleep_ms(120)

    def init(self):
        for cmd, data in (
            (0xEF, b"\x03\x80\x02"),
            (0xCF, b"\x00\xC1\x30"),
            (0xED, b"\x64\x03\x12\x81"),
            (0xE8, b"\x85\x00\x78"),
            (0xCB, b"\x39\x2C\x00\x34\x02"),
            (0xF7, b"\x20"),
            (0xEA, b"\x00\x00"),
            (0xC0, b"\x23"),          # power control 1
            (0xC1, b"\x10"),          # power control 2
            (0xC5, b"\x3E\x28"),      # VCOM control 1
            (0xC7, b"\x86"),          # VCOM control 2
            (0x36, bytes([self._madctl])),  # memory access / rotation
            (0x3A, b"\x55"),          # 16 bits per pixel
            (0xB1, b"\x00\x18"),      # frame rate
            (0xB6, b"\x08\x82\x27"),  # display function control
            (0xF2, b"\x00"),          # 3-gamma off
            (0x26, b"\x01"),          # gamma curve
            (0xE0, b"\x0F\x31\x2B\x0C\x0E\x08\x4E\xF1\x37\x07\x10\x03\x0E\x09\x00"),
            (0xE1, b"\x00\x0E\x14\x03\x11\x07\x31\xC1\x48\x08\x0F\x0C\x31\x36\x0F"),
        ):
            self._cmd(cmd, data)
        self._cmd(0x11)  # sleep out
        time.sleep_ms(120)
        self._cmd(0x29)  # display on

    def sleep(self, on=True):
        self._cmd(0x10 if on else 0x11)
        time.sleep_ms(5 if on else 120)

    def _window(self, x0, y0, x1, y1):
        self._cmd(0x2A, bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._cmd(0x2B, bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))

    def blit(self, x, y, w, h, buf):
        """Write a raw RGB565 (big-endian) buffer to a rectangle."""
        if w <= 0 or h <= 0:
            return
        self._window(x, y, x + w - 1, y + h - 1)
        self._cmd(0x2C, buf)

    # ---------- drawing ----------
    def fill_rect(self, x, y, w, h, color):
        # clip to screen
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        w = min(w, self.width - x)
        h = min(h, self.height - y)
        if w <= 0 or h <= 0:
            return
        self._window(x, y, x + w - 1, y + h - 1)
        px = bytes([color >> 8, color & 0xFF])
        total = w * h
        chunk = min(total, 1024)
        line = px * chunk
        self.cs(0)
        self.dc(0)
        self.spi.write(b"\x2C")
        self.dc(1)
        while total > 0:
            n = min(total, chunk)
            self.spi.write(line if n == chunk else line[: n * 2])
            total -= n
        self.cs(1)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def pixel(self, x, y, color):
        self.fill_rect(x, y, 1, 1, color)

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def rect(self, x, y, w, h, color, thickness=1):
        t = thickness
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def round_rect(self, x, y, w, h, r, color):
        """Filled rectangle with rounded corners."""
        self.fill_rect(x + r, y, w - 2 * r, h, color)
        for i in range(r):
            # simple quarter-circle steps
            dy = r - i
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(x + r - dx, y + i, dx, 1, color)
            self.fill_rect(x + w - r, y + i, dx, 1, color)
            self.fill_rect(x + r - dx, y + h - 1 - i, dx, 1, color)
            self.fill_rect(x + w - r, y + h - 1 - i, dx, 1, color)
        self.fill_rect(x, y + r, r, h - 2 * r, color)
        self.fill_rect(x + w - r, y + r, r, h - 2 * r, color)

    def bitmap(self, rows, x, y, scale, color):
        """Draw a tiny picture given as list of strings ('#' = on)."""
        for j, row in enumerate(rows):
            i = 0
            while i < len(row):
                if row[i] == "#":
                    start = i
                    while i < len(row) and row[i] == "#":
                        i += 1
                    self.fill_rect(x + start * scale, y + j * scale,
                                   (i - start) * scale, scale, color)
                else:
                    i += 1

    # ---------- text (built-in 8x8 font, scalable) ----------
    def text(self, s, x, y, fg, bg, scale=1):
        """Draw text. Each character is 8*scale pixels wide and tall."""
        fgb = bytes([fg >> 8, fg & 0xFF]) * scale
        bgb = bytes([bg >> 8, bg & 0xFF]) * scale
        size = 8 * scale
        for ch in s:
            if x + size > self.width:
                break
            self._glyph_fb.fill(0)
            self._glyph_fb.text(ch, 0, 0, 1)
            out = bytearray()
            for row in self._glyph:
                line = b"".join([fgb if row & (0x80 >> b) else bgb for b in range(8)])
                out += line * scale
            self.blit(x, y, size, size, out)
            x += size

    @staticmethod
    def text_width(s, scale=1):
        return len(s) * 8 * scale

    def center_text(self, s, y, fg, bg, scale=1, x=0, w=None):
        w = self.width if w is None else w
        tx = x + (w - self.text_width(s, scale)) // 2
        self.text(s, tx, y, fg, bg, scale)
