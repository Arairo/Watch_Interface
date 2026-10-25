# ---------------------------------------------------------------
#  xpt2046.py - resistive touch controller used on ILI9341 boards
# ---------------------------------------------------------------
from machine import Pin

_CMD_X = 0xD0
_CMD_Y = 0x90
_CMD_Z1 = 0xB0


class XPT2046:
    def __init__(self, spi, cs, irq=None, width=320, height=240,
                 x_min=200, x_max=3900, y_min=200, y_max=3900,
                 swap_xy=True, invert_x=False, invert_y=True):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.irq = Pin(irq, Pin.IN) if irq is not None else None
        self.width = width
        self.height = height
        self.x_min, self.x_max = x_min, x_max
        self.y_min, self.y_max = y_min, y_max
        self.swap_xy = swap_xy
        self.invert_x = invert_x
        self.invert_y = invert_y
        self._tx = bytearray(3)
        self._rx = bytearray(3)

    def _read(self, cmd):
        self._tx[0] = cmd
        self.cs(0)
        self.spi.write_readinto(self._tx, self._rx)
        self.cs(1)
        return ((self._rx[1] << 8) | self._rx[2]) >> 3

    def is_touched(self):
        if self.irq is not None:
            return self.irq.value() == 0
        return self._read(_CMD_Z1) > 100

    def raw(self, samples=6):
        """Average a few raw 12-bit readings. Returns (x, y) or None."""
        if not self.is_touched():
            return None
        xs, ys = [], []
        for _ in range(samples):
            x = self._read(_CMD_X)
            y = self._read(_CMD_Y)
            if 50 < x < 4050 and 50 < y < 4050:
                xs.append(x)
                ys.append(y)
        if len(xs) < samples // 2 or not self.is_touched():
            return None
        xs.sort()
        ys.sort()
        return xs[len(xs) // 2], ys[len(ys) // 2]   # median = less jitter

    def get(self):
        """Return touch position in screen pixels, or None."""
        r = self.raw()
        if r is None:
            return None
        rx, ry = r
        if self.swap_xy:
            rx, ry = ry, rx
        x = (rx - self.x_min) * self.width // (self.x_max - self.x_min)
        y = (ry - self.y_min) * self.height // (self.y_max - self.y_min)
        if self.invert_x:
            x = self.width - 1 - x
        if self.invert_y:
            y = self.height - 1 - y
        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))
        return x, y
