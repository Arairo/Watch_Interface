# ---------------------------------------------------------------
#  config.py  -  Hardware + personal settings
#  Change these values to match YOUR wiring and YOUR teacher.
# ---------------------------------------------------------------

# ---- Personalisation ------------------------------------------
TEACHER_NAME = "Teacher"        # e.g. "Mr. Smith" or "Ms. Lopez"
STUDENT_NAME = "Your Student"   # who the gift is from

# ---- ILI9341 display (hardware SPI, VSPI) ---------------------
TFT_SPI_ID = 2          # 2 = VSPI on ESP32
TFT_BAUD   = 40_000_000 # drop to 20_000_000 if you see glitches
TFT_SCK    = 18
TFT_MOSI   = 23
TFT_MISO   = 19
TFT_CS     = 15
TFT_DC     = 2
TFT_RST    = 4
TFT_LED    = 21         # backlight pin (PWM for brightness)

# Screen is used in landscape: 320 x 240
TFT_WIDTH  = 320
TFT_HEIGHT = 240
# MADCTL value for landscape. 0x28 works on most boards.
# If the picture is mirrored/upside-down try 0xE8, 0x68 or 0xA8.
TFT_MADCTL = 0x28

# ---- XPT2046 touch controller (software SPI, own pins) --------
TOUCH_SCK  = 25
TOUCH_MOSI = 32         # T_DIN
TOUCH_MISO = 39         # T_DO  (input-only pin is fine)
TOUCH_CS   = 33
TOUCH_IRQ  = 34         # T_IRQ (goes LOW while touched)

# Touch calibration. Run calibrate.py once and paste the numbers here.
TOUCH_X_MIN = 200
TOUCH_X_MAX = 3900
TOUCH_Y_MIN = 200
TOUCH_Y_MAX = 3900
TOUCH_SWAP_XY  = True   # landscape usually needs X/Y swapped
TOUCH_INVERT_X = False
TOUCH_INVERT_Y = True

# ---- Battery sense (LiPo through a 100k/100k voltage divider) -
BATTERY_ADC_PIN = 35    # set to None if you didn't wire the divider
BATTERY_DIVIDER = 2.0   # (R1 + R2) / R2
BATTERY_FULL_V  = 4.20
BATTERY_EMPTY_V = 3.30

# ---- Optional buzzer for Pomodoro alarm (None = no buzzer) ----
BUZZER_PIN = None       # e.g. 26

# ---- Power saving --------------------------------------------
DIM_AFTER_S   = 60      # dim backlight after this many idle seconds
SLEEP_AFTER_S = 300     # turn backlight off after this many idle seconds
DEFAULT_BRIGHTNESS = 80 # percent

# ---- Pomodoro defaults (minutes) ------------------------------
POMO_WORK  = 25
POMO_SHORT = 5
POMO_LONG  = 15
POMO_ROUNDS_BEFORE_LONG = 4
