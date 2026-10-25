# Teacher Gift – ESP32 Touch Interface

A small handheld touch-screen gadget made as a gift from a student to a teacher.
Written in **MicroPython** for an **ESP32** with a **2.4" ILI9341 TFT touch screen**,
powered by a **3.7 V LiPo** charged through a **TP4056** module.

## Features

| Button | What it does |
|---|---|
| **Kudos!** | Shows a random compliment ("Best teacher ever!" and 20+ more) with a heart and confetti. Never shows the same one twice in a row. |
| **Pomodoro** | 25 min focus / 5 min short break / 15 min long break after 4 rounds. Start, Pause, Reset, Skip, progress bar and round counter. Keeps running while you use other screens (a mini countdown shows in the top bar) and flashes the screen when time is up. |
| **Quotes** | Inspiring quotes about learning and teaching. |
| **Fun Fact** | Random fun facts to share with the class. |
| **Breaks** | Quick "brain break" ideas, which go well with the Pomodoro breaks. |
| **Thank You** | A personal multi-page thank-you note from the student. |
| **Class Kit** | Classroom helpers: coin flip, dice roll, and a random number picker (1–N, adjustable) for picking students. |
| **Settings** | Screen brightness, battery voltage, and a "made with love by" credit. |

Also included:
- Battery level icon in the top bar
- Power saving: the screen dims after 60 s and turns off after 5 min (unless the Pomodoro is running). The first tap only wakes it.
- A splash screen: "For the BEST TEACHER".

## Files

```
main.py        the app (runs automatically on boot)
config.py      pins, teacher/student names, timer lengths, calibration
content.py     all compliments, quotes, facts, break ideas, thank-you note
calibrate.py   one-time touch calibration helper
lib/ili9341.py display driver (low RAM, no PSRAM needed)
lib/xpt2046.py touch driver
```

**To personalise it:** edit `TEACHER_NAME` and `STUDENT_NAME` in `config.py`, and
rewrite the text in `content.py`. Use plain ASCII characters only, because the built-in font has no emoji or accents.

## Wiring

### Display (ILI9341) → ESP32

| TFT pin | ESP32 GPIO |
|---|---|
| VCC | 3V3 |
| GND | GND |
| CS | 15 |
| RESET | 4 |
| DC / RS | 2 |
| SDI / MOSI | 23 |
| SCK | 18 |
| LED | 21 (or 3V3 for always-on, but then brightness control won't work) |
| SDO / MISO | 19 |

### Touch (XPT2046, same board) → ESP32

| Touch pin | ESP32 GPIO |
|---|---|
| T_CLK | 25 |
| T_CS | 33 |
| T_DIN | 32 |
| T_DO | 39 (VN) |
| T_IRQ | 34 |

You can change any pin in `config.py`.

### Power

```
 LiPo +  ──► TP4056 B+          TP4056 OUT+ ──► switch ──► 3.3 V LDO IN ──► ESP32 3V3
 LiPo −  ──► TP4056 B−          TP4056 OUT− ─────────────────────────────► ESP32 GND
 USB-C/micro on the TP4056 charges the battery
```

- Use the **TP4056 board with the protection chip** (6 pins: IN+, IN−, B+, B−, OUT+, OUT−). It stops the battery from over-discharging.
- A LiPo goes from 4.2 V (full) to about 3.3 V (empty). The ESP32 needs a steady 3.3 V, so feed it through a
  **low-dropout regulator** (e.g. HT7333, MCP1700-3302 or AP2112K-3.3) into the **3V3** pin.
  The AMS1117 on most dev boards needs about 4.3 V+ on VIN, so powering through VIN/5V only works while the battery is nearly full.
- **Don't** connect USB to the ESP32 and the battery at the same time unless your board has a diode to keep them apart.
- Add a small slide switch on OUT+ so the teacher can turn it off.

### Battery level (optional)

Two 100 kΩ resistors in series from **TP4056 OUT+** to **GND**, with the middle point to **GPIO 35**.
If you skip this, set `BATTERY_ADC_PIN = None` in `config.py` and the icon shows "?".

### Buzzer (optional)

An active buzzer on a free GPIO (e.g. 26) beeps when a Pomodoro ends. Set `BUZZER_PIN = 26`.

## Installing

1. **Flash MicroPython** onto the ESP32: download the latest ESP32 firmware from
   <https://micropython.org/download/ESP32_GENERIC/>. The easiest way is **Thonny**:
   *Tools → Options → Interpreter → MicroPython (ESP32) → Install or update MicroPython*.
2. In Thonny, upload the files to the board (*View → Files*, right-click → *Upload to /*):
   - `main.py`, `config.py`, `content.py`, `calibrate.py` → `/`
   - create a folder `lib` on the board and upload `lib/ili9341.py`, `lib/xpt2046.py` into it
3. **Calibrate the touch:** open `calibrate.py` in Thonny, press **Run**, tap the 4 crosses,
   and copy the printed `TOUCH_...` lines into `config.py` on the board.
4. Press the **EN/RESET** button. The splash screen appears, followed by the home menu.

### Troubleshooting

- **White or blank screen:** check the CS, DC and RESET wiring, or lower `TFT_BAUD` to `20_000_000`.
- **Picture mirrored or upside-down:** try `TFT_MADCTL = 0xE8` (or `0x68`, `0xA8`).
- **Taps land in the wrong place:** re-run `calibrate.py`, or flip `TOUCH_SWAP_XY` / `TOUCH_INVERT_*`.
- **Wrong colours (red and blue swapped):** change `TFT_MADCTL` 0x28 → 0x20 (removes the BGR bit).

## Battery life

The screen and ESP32 draw about 80–120 mA, so a 1000 mAh LiPo lasts roughly 8–10 hours of screen-on time.
Auto-dimming and screen-off stretch that a lot. Switch it off with the slide switch overnight.

Made with ❤ by a grateful student.
