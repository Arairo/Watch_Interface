# ---------------------------------------------------------------
#  main.py - "Teacher Gift" touch interface for ESP32 + ILI9341
#
#  Screens:  Kudos (compliments) | Pomodoro | Quotes | Fun Fact
#            Breaks | Thank You note | Class Kit | Settings
#
#  MicroPython runs main.py automatically on boot.
# ---------------------------------------------------------------
import time
import random
from machine import Pin, SPI, SoftSPI, PWM, ADC

import config as C
import content
from ili9341 import ILI9341, color565
from xpt2046 import XPT2046

# ---------------- colours ----------------
BG      = color565(18, 22, 48)     # deep navy
PANEL   = color565(34, 40, 82)
WHITE   = color565(255, 255, 255)
GREY    = color565(150, 156, 190)
BLACK   = 0
PINK    = color565(255, 105, 150)
RED     = color565(235, 70, 70)
ORANGE  = color565(255, 150, 60)
YELLOW  = color565(255, 214, 70)
GREEN   = color565(80, 210, 120)
TEAL    = color565(50, 200, 200)
BLUE    = color565(80, 140, 255)
PURPLE  = color565(165, 110, 255)
CONFETTI = (PINK, YELLOW, GREEN, TEAL, BLUE, PURPLE, ORANGE)

HEART = [
    ".##...##.",
    "####.####",
    "#########",
    "#########",
    ".#######.",
    "..#####..",
    "...###...",
    "....#....",
]
APPLE = [
    ".....#...",
    "....#....",
    ".##.#.##.",
    "#########",
    "#########",
    "#########",
    ".#######.",
    "..##.##..",
]

HEADER_H = 32


# ---------------- hardware ----------------
spi = SPI(C.TFT_SPI_ID, baudrate=C.TFT_BAUD, sck=Pin(C.TFT_SCK),
          mosi=Pin(C.TFT_MOSI), miso=Pin(C.TFT_MISO))
tft = ILI9341(spi, C.TFT_CS, C.TFT_DC, C.TFT_RST,
              C.TFT_WIDTH, C.TFT_HEIGHT, C.TFT_MADCTL)

tspi = SoftSPI(baudrate=1_000_000, sck=Pin(C.TOUCH_SCK),
               mosi=Pin(C.TOUCH_MOSI), miso=Pin(C.TOUCH_MISO))
touch = XPT2046(tspi, C.TOUCH_CS, C.TOUCH_IRQ, C.TFT_WIDTH, C.TFT_HEIGHT,
                C.TOUCH_X_MIN, C.TOUCH_X_MAX, C.TOUCH_Y_MIN, C.TOUCH_Y_MAX,
                C.TOUCH_SWAP_XY, C.TOUCH_INVERT_X, C.TOUCH_INVERT_Y)


class Backlight:
    def __init__(self, pin, percent):
        self.pwm = PWM(Pin(pin), freq=2000)
        self.level = percent      # user setting
        self.set(percent)

    def set(self, percent):
        percent = max(0, min(100, percent))
        if hasattr(self.pwm, "duty_u16"):
            self.pwm.duty_u16(percent * 65535 // 100)
        else:
            self.pwm.duty(percent * 1023 // 100)


class Battery:
    def __init__(self, pin):
        self.adc = None
        if pin is not None:
            self.adc = ADC(Pin(pin))
            self.adc.atten(ADC.ATTN_11DB)   # full 0-3.3 V range

    def voltage(self):
        if self.adc is None:
            return None
        if hasattr(self.adc, "read_uv"):    # factory-calibrated reading
            total = sum(self.adc.read_uv() for _ in range(16)) / 16
            v = total / 1_000_000
        else:
            total = sum(self.adc.read() for _ in range(16)) / 16
            v = total / 4095 * 3.3
        return v * C.BATTERY_DIVIDER

    def percent(self):
        v = self.voltage()
        if v is None:
            return None
        p = (v - C.BATTERY_EMPTY_V) / (C.BATTERY_FULL_V - C.BATTERY_EMPTY_V)
        return int(max(0, min(1, p)) * 100)


backlight = Backlight(C.TFT_LED, C.DEFAULT_BRIGHTNESS)
battery = Battery(C.BATTERY_ADC_PIN)
buzzer = Pin(C.BUZZER_PIN, Pin.OUT, value=0) if C.BUZZER_PIN is not None else None


# ---------------- helpers ----------------
def wrap(text, width):
    """Split text into lines of at most `width` characters."""
    lines, line = [], ""
    for word in text.split():
        while len(word) > width:            # very long word
            if line:
                lines.append(line)
                line = ""
            lines.append(word[:width])
            word = word[width:]
        if not line:
            line = word
        elif len(line) + 1 + len(word) <= width:
            line += " " + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_lines(lines, y_top, y_bottom, color, scale=2, bg=BG):
    """Draw centred lines, vertically centred between y_top/y_bottom."""
    lh = 8 * scale + 6
    total = len(lines) * lh - 6
    y = y_top + max(0, (y_bottom - y_top - total) // 2)
    for ln in lines:
        tft.center_text(ln, y, color, bg, scale)
        y += lh


def pick_new(items, last):
    """Random index that is different from the last one."""
    if len(items) < 2:
        return 0
    i = last
    while i == last:
        i = random.randint(0, len(items) - 1)
    return i


def confetti(n=24):
    """Sprinkle coloured squares down the left and right edges."""
    for _ in range(n):
        x = random.choice((random.randint(2, 30), random.randint(282, 310)))
        y = random.randint(HEADER_H + 4, 180)
        s = random.randint(4, 8)
        tft.fill_rect(x, y, s, s, random.choice(CONFETTI))


def fmt_time(ms):
    s = max(0, (ms + 999) // 1000)
    return "%02d:%02d" % (s // 60, s % 60)


def beep(times=3):
    if buzzer is None:
        return
    for _ in range(times):
        buzzer(1)
        time.sleep_ms(120)
        buzzer(0)
        time.sleep_ms(120)


# ---------------- widgets ----------------
class Button:
    def __init__(self, x, y, w, h, label, color, cb, text_color=WHITE, scale=2):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label
        self.color = color
        self.cb = cb
        self.text_color = text_color
        self.scale = scale

    def hit(self, px, py):
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h

    def draw(self, pressed=False):
        col = WHITE if pressed else self.color
        txt = self.color if pressed else self.text_color
        tft.round_rect(self.x, self.y, self.w, self.h, 8, col)
        th = 8 * self.scale
        tft.center_text(self.label, self.y + (self.h - th) // 2, txt, col,
                        self.scale, self.x, self.w)


# ---------------- Pomodoro engine (runs on every screen) -------------
class Pomodoro:
    LABELS = {"work": "FOCUS", "short": "SHORT BREAK", "long": "LONG BREAK"}
    COLORS = {"work": RED, "short": GREEN, "long": TEAL}

    def __init__(self):
        self.minutes = {"work": C.POMO_WORK, "short": C.POMO_SHORT,
                        "long": C.POMO_LONG}
        self.rounds = 0
        self.set_mode("work")

    def set_mode(self, mode):
        self.mode = mode
        self.total_ms = self.minutes[mode] * 60_000
        self.remaining = self.total_ms
        self.running = False

    def start(self):
        self.running = True
        self.end = time.ticks_add(time.ticks_ms(), self.remaining)

    def pause(self):
        self.remaining = self.left()
        self.running = False

    def left(self):
        if not self.running:
            return self.remaining
        return max(0, time.ticks_diff(self.end, time.ticks_ms()))

    def next_mode(self):
        if self.mode == "work":
            self.rounds += 1
            if self.rounds % C.POMO_ROUNDS_BEFORE_LONG == 0:
                self.set_mode("long")
            else:
                self.set_mode("short")
        else:
            self.set_mode("work")

    def finished(self):
        """True once when a running timer hits zero."""
        if self.running and self.left() == 0:
            self.next_mode()
            return True
        return False


pomo = Pomodoro()


# ---------------- screens ----------------
class Screen:
    title = ""
    has_back = True

    def __init__(self, app):
        self.app = app
        self.buttons = []

    def enter(self):
        self.draw()

    def draw(self):
        tft.fill(BG)
        self.app.draw_header(self.title, self.has_back)
        self.draw_body()
        for b in self.buttons:
            b.draw()

    def draw_body(self):
        pass

    def tick(self):
        pass


class Home(Screen):
    has_back = False

    def __init__(self, app):
        super().__init__(app)
        self.title = "Hi, %s!" % C.TEACHER_NAME
        items = [
            ("Kudos!", PINK, "kudos"),
            ("Pomodoro", RED, "pomo"),
            ("Quotes", PURPLE, "quotes"),
            ("Fun Fact", BLUE, "facts"),
            ("Breaks", GREEN, "breaks"),
            ("Thank You", ORANGE, "thanks"),
            ("Class Kit", TEAL, "kit"),
            ("Settings", PANEL, "settings"),
        ]
        bw, bh, gap = 152, 46, 4
        for i, (label, col, target) in enumerate(items):
            x = 5 + (i % 2) * (bw + 6)
            y = HEADER_H + 8 + (i // 2) * (bh + gap)
            self.buttons.append(
                Button(x, y, bw, bh, label, col,
                       lambda t=target: self.app.go(t)))


class CardScreen(Screen):
    """Shows one random (or sequential) item from a list."""

    def __init__(self, app, title, items, color, button_text, picture=None,
                 pic_color=None, celebrate=False):
        super().__init__(app)
        self.title = title
        self.items = items
        self.color = color
        self.picture = picture
        self.pic_color = pic_color or color
        self.celebrate = celebrate
        self.index = -1
        self.count = 0
        self.buttons = [Button(70, 190, 180, 42, button_text, color, self.next)]

    def enter(self):
        self.index = pick_new(self.items, self.index)
        self.count += 1
        self.draw()

    def next(self):
        self.index = pick_new(self.items, self.index)
        self.count += 1
        self.redraw_card()

    def text_and_footer(self):
        item = self.items[self.index]
        if isinstance(item, tuple):
            return item[0], "- " + item[1]
        return item, None

    def draw_body(self):
        self.redraw_card(clear=False)

    def redraw_card(self, clear=True):
        if clear:
            tft.fill_rect(0, HEADER_H, tft.width, 190 - HEADER_H - 2, BG)
        if self.celebrate and clear:
            confetti()           # drawn first so the text sits on top
        top = HEADER_H + 6
        if self.picture:
            tft.bitmap(self.picture, (tft.width - 9 * 4) // 2, top, 4, self.pic_color)
            top += 8 * 4 + 6
        text, footer = self.text_and_footer()
        lines = wrap(text, 19)
        scale = 2
        if len(lines) * 22 > (180 - top):
            lines, scale = wrap(text, 38), 1
        bottom = 170 if footer else 184
        draw_lines(lines, top, bottom, WHITE, scale)
        if footer:
            tft.center_text(footer, 174, GREY, BG, 1)


class ThankYou(CardScreen):
    def __init__(self, app):
        pages = [p.format(teacher=C.TEACHER_NAME, student=C.STUDENT_NAME)
                 for p in content.THANK_YOU_PAGES]
        super().__init__(app, "Thank You", pages, ORANGE, "Next >",
                         picture=HEART, pic_color=PINK)
        self.buttons = [
            Button(10, 190, 140, 42, "< Prev", PANEL, self.prev),
            Button(170, 190, 140, 42, "Next >", ORANGE, self.next),
        ]

    def enter(self):
        self.index = 0
        self.draw()

    def next(self):
        self.index = (self.index + 1) % len(self.items)
        self.redraw_card()

    def prev(self):
        self.index = (self.index - 1) % len(self.items)
        self.redraw_card()

    def text_and_footer(self):
        return self.items[self.index], "page %d of %d" % (self.index + 1, len(self.items))


class PomodoroScreen(Screen):
    title = "Pomodoro"

    def __init__(self, app):
        super().__init__(app)
        self.start_btn = Button(8, 188, 120, 44, "Start", GREEN, self.toggle)
        self.buttons = [
            self.start_btn,
            Button(136, 188, 84, 44, "Reset", PANEL, self.reset),
            Button(228, 188, 84, 44, "Skip", PANEL, self.skip),
        ]
        self.shown = None

    def enter(self):
        self.update_labels()
        self.draw()

    def update_labels(self):
        self.start_btn.label = "Pause" if pomo.running else "Start"
        self.start_btn.color = ORANGE if pomo.running else GREEN

    def draw_body(self):
        col = Pomodoro.COLORS[pomo.mode]
        tft.fill_rect(0, HEADER_H, tft.width, 150, BG)
        tft.center_text(Pomodoro.LABELS[pomo.mode], HEADER_H + 10, col, BG, 2)
        self.shown = None
        self.draw_time(force=True)
        # round counter: filled dot = finished focus session
        n = C.POMO_ROUNDS_BEFORE_LONG
        done = pomo.rounds % n
        x0 = (tft.width - (n * 22 - 8)) // 2
        for i in range(n):
            c = RED if i < done else PANEL
            tft.round_rect(x0 + i * 22, 162, 14, 14, 4, c)
        tft.text("rounds: %d" % pomo.rounds, 8, 166, GREY, BG, 1)

    def draw_time(self, force=False):
        left = pomo.left()
        s = fmt_time(left)
        if s == self.shown and not force:
            return
        self.shown = s
        col = Pomodoro.COLORS[pomo.mode]
        tft.center_text(s, HEADER_H + 40, WHITE, BG, 6)
        # progress bar
        bx, by, bw, bh = 20, HEADER_H + 100, 280, 14
        done = (pomo.total_ms - left) * bw // max(1, pomo.total_ms)
        tft.fill_rect(bx, by, done, bh, col)
        tft.fill_rect(bx + done, by, bw - done, bh, PANEL)

    def toggle(self):
        pomo.pause() if pomo.running else pomo.start()
        self.update_labels()

    def reset(self):
        pomo.set_mode(pomo.mode)
        self.update_labels()
        self.draw_body()

    def skip(self):
        pomo.next_mode()
        self.update_labels()
        self.draw_body()

    def tick(self):
        self.draw_time()

    def on_finished(self):
        # flash the screen in the colour of the next phase
        col = Pomodoro.COLORS[pomo.mode]
        for _ in range(3):
            tft.fill(col)
            time.sleep_ms(150)
            tft.fill(BG)
            time.sleep_ms(150)
        beep()
        self.update_labels()
        self.draw()
        msg = "Time to focus!" if pomo.mode == "work" else "Break time!"
        tft.fill_rect(0, HEADER_H + 100, tft.width, 16, BG)
        tft.center_text(msg, HEADER_H + 100, YELLOW, BG, 2)


class ClassKit(Screen):
    title = "Class Kit"

    def __init__(self, app):
        super().__init__(app)
        self.max_n = 30
        self.n_btn = Button(110, 192, 100, 40, "1-30", PANEL, lambda: None)
        self.buttons = [
            Button(6, HEADER_H + 6, 98, 40, "Coin", YELLOW, self.coin, BLACK),
            Button(111, HEADER_H + 6, 98, 40, "Dice", PINK, self.dice),
            Button(216, HEADER_H + 6, 98, 40, "Pick #", TEAL, self.number),
            Button(10, 192, 90, 40, "-", PANEL, lambda: self.change(-1), scale=3),
            self.n_btn,
            Button(220, 192, 90, 40, "+", PANEL, lambda: self.change(1), scale=3),
        ]

    def draw_body(self):
        self.clear_result()
        tft.center_text("Tap a tool!", 120, GREY, BG, 2)

    def clear_result(self):
        tft.fill_rect(0, HEADER_H + 50, tft.width, 106, BG)

    def coin(self):
        for i in range(6):                     # little flip animation
            self.clear_result()
            tft.center_text("HEADS" if i % 2 else "TAILS", 115, GREY, BG, 4)
            time.sleep_ms(70)
        self.clear_result()
        tft.center_text(random.choice(("HEADS", "TAILS")), 115, YELLOW, BG, 5)

    def dice(self):
        for _ in range(5):
            self.draw_die(random.randint(1, 6), GREY)
            time.sleep_ms(70)
        self.draw_die(random.randint(1, 6), WHITE)

    def draw_die(self, v, col):
        self.clear_result()
        s, x, y = 96, (tft.width - 96) // 2, HEADER_H + 54
        tft.round_rect(x, y, s, s, 12, col)
        pips = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)],
                4: [(0, 0), (2, 0), (0, 2), (2, 2)],
                5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
                6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}[v]
        for px, py in pips:
            tft.round_rect(x + 14 + px * 26, y + 14 + py * 26, 16, 16, 6, BLACK)

    def number(self):
        for _ in range(6):
            self.clear_result()
            tft.center_text(str(random.randint(1, self.max_n)), 100, GREY, BG, 6)
            time.sleep_ms(60)
        self.clear_result()
        tft.center_text(str(random.randint(1, self.max_n)), 100, TEAL, BG, 7)

    def change(self, d):
        self.max_n = max(2, min(99, self.max_n + d))
        self.n_btn.label = "1-%d" % self.max_n
        self.n_btn.draw()


class Settings(Screen):
    title = "Settings"

    def __init__(self, app):
        super().__init__(app)
        self.buttons = [
            Button(10, HEADER_H + 30, 70, 40, "-", PANEL, lambda: self.bright(-10), scale=3),
            Button(240, HEADER_H + 30, 70, 40, "+", PANEL, lambda: self.bright(10), scale=3),
        ]

    def bright(self, d):
        backlight.level = max(10, min(100, backlight.level + d))
        backlight.set(backlight.level)
        self.draw_bar()

    def draw_bar(self):
        x, y, w, h = 90, HEADER_H + 42, 140, 16
        fill = (backlight.level * w) // 100
        tft.fill_rect(x, y, fill, h, YELLOW)
        tft.fill_rect(x + fill, y, w - fill, h, PANEL)

    def draw_body(self):
        tft.center_text("Brightness", HEADER_H + 10, WHITE, BG, 2)
        self.draw_bar()
        v = battery.voltage()
        btxt = "Battery: not wired" if v is None else \
            "Battery: %.2f V (%d%%)" % (v, battery.percent())
        tft.center_text(btxt, HEADER_H + 90, WHITE, BG, 1)
        tft.center_text("Dims after %ds, sleeps after %ds" %
                        (C.DIM_AFTER_S, C.SLEEP_AFTER_S), HEADER_H + 106, GREY, BG, 1)
        tft.bitmap(APPLE, (tft.width - 9 * 4) // 2, HEADER_H + 126, 4, RED)
        tft.center_text("Made with love by", HEADER_H + 166, GREY, BG, 1)
        tft.center_text(C.STUDENT_NAME, HEADER_H + 180, PINK, BG, 2)


# ---------------- app / main loop ----------------
class App:
    def __init__(self):
        self.screens = {
            "home": Home(self),
            "kudos": CardScreen(self, "Kudos!", content.COMPLIMENTS, PINK,
                                "Another!", HEART, celebrate=True),
            "pomo": PomodoroScreen(self),
            "quotes": CardScreen(self, "Quotes", content.QUOTES, PURPLE, "Next"),
            "facts": CardScreen(self, "Fun Fact", content.FUN_FACTS, BLUE, "Another"),
            "breaks": CardScreen(self, "Breaks", content.BREAK_IDEAS, GREEN,
                                 "Another", APPLE, pic_color=RED),
            "thanks": ThankYou(self),
            "kit": ClassKit(self),
            "settings": Settings(self),
        }
        self.current = None
        self.name = None
        self.last_touch = time.ticks_ms()
        self.power = "on"   # on / dim / off
        self.last_header = time.ticks_ms()

    # ----- navigation -----
    def go(self, name):
        self.name = name
        self.current = self.screens[name]
        self.current.enter()

    # ----- header bar -----
    def draw_header(self, title, back):
        tft.fill_rect(0, 0, tft.width, HEADER_H, PANEL)
        if back:
            tft.text("<", 12, 8, WHITE, PANEL, 2)
        # title lives between the back arrow and the status icons
        if len(title) <= 10:
            tft.center_text(title, 8, WHITE, PANEL, 2, 50, 172)
        else:
            tft.center_text(title[:21], 12, WHITE, PANEL, 1, 50, 172)
        self.draw_status()

    def draw_status(self):
        # mini pomodoro countdown when it runs in the background
        tft.fill_rect(222, 0, 54, HEADER_H, PANEL)
        if pomo.running and self.name != "pomo":
            tft.text(fmt_time(pomo.left()), 230, 12, Pomodoro.COLORS[pomo.mode], PANEL, 1)
        # battery icon
        x, y = 282, 10
        tft.rect(x, y, 26, 12, WHITE)
        tft.fill_rect(x + 26, y + 3, 3, 6, WHITE)
        p = battery.percent()
        tft.fill_rect(x + 2, y + 2, 22, 8, PANEL)
        if p is None:
            tft.text("?", x + 9, y + 2, GREY, PANEL, 1)
        else:
            col = GREEN if p > 50 else YELLOW if p > 20 else RED
            tft.fill_rect(x + 2, y + 2, max(1, 22 * p // 100), 8, col)

    # ----- power saving -----
    def wake(self):
        if self.power == "off":
            tft.sleep(False)
        self.power = "on"
        backlight.set(backlight.level)

    def check_idle(self):
        idle = time.ticks_diff(time.ticks_ms(), self.last_touch) // 1000
        if self.power == "on" and idle >= C.DIM_AFTER_S:
            self.power = "dim"
            backlight.set(max(5, backlight.level // 5))
        elif self.power == "dim" and idle >= C.SLEEP_AFTER_S and not pomo.running:
            self.power = "off"
            backlight.set(0)
            tft.sleep(True)

    # ----- touch handling -----
    def handle_touch(self, x, y):
        if self.current.has_back and x < 50 and y < HEADER_H:
            self.go("home")
            return
        for b in self.current.buttons:
            if b.hit(x, y):
                b.draw(pressed=True)
                time.sleep_ms(60)
                before = self.current
                b.cb()
                if self.current is before and b in self.current.buttons:
                    b.draw()
                return

    def splash(self):
        tft.fill(BG)
        tft.bitmap(HEART, (tft.width - 9 * 8) // 2, 40, 8, PINK)
        tft.center_text("For the", 120, GREY, BG, 2)
        tft.center_text("BEST TEACHER", 145, YELLOW, BG, 3)
        tft.center_text(C.TEACHER_NAME, 185, WHITE, BG, 2)
        time.sleep_ms(1800)

    def run(self):
        self.splash()
        self.go("home")
        was_down = False
        while True:
            pos = touch.get()
            if pos and not was_down:
                was_down = True
                self.last_touch = time.ticks_ms()
                if self.power != "on":
                    self.wake()          # first tap only wakes the screen
                else:
                    self.handle_touch(*pos)
            elif not pos and not touch.is_touched():
                was_down = False

            if pomo.finished():
                self.last_touch = time.ticks_ms()
                self.wake()
                if self.name != "pomo":
                    self.go("pomo")
                self.screens["pomo"].on_finished()

            self.current.tick()

            # refresh header status every second
            if time.ticks_diff(time.ticks_ms(), self.last_header) > 1000:
                self.last_header = time.ticks_ms()
                if self.power != "off":
                    self.draw_status()

            self.check_idle()
            time.sleep_ms(20)


App().run()
