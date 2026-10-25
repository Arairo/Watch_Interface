# Teacher Gift – ESP32 Touch Gadget

A little touch-screen gadget made as a thank-you gift for a teacher.
It shows compliments ("Best teacher ever!"), runs a Pomodoro timer, shows quotes and fun facts,
and has classroom tools: a coin flip, a dice roll and a random number picker.

This guide goes **one tiny step at a time**. Do the steps in order. Don't skip any.

---

## Contents

1. [What the gadget does](#1-what-the-gadget-does)
2. [Shopping list](#2-shopping-list)
3. [Tools you need](#3-tools-you-need)
4. [Safety first](#4-safety-first)
5. [Step A – Put the program on the ESP32 (no soldering yet)](#step-a--put-the-program-on-the-esp32-no-soldering-yet)
6. [Step B – Connect the screen](#step-b--connect-the-screen)
7. [Step C – Test it with USB power](#step-c--test-it-with-usb-power)
8. [Step D – Make the touch work properly (calibrate)](#step-d--make-the-touch-work-properly-calibrate)
9. [Step E – Build the battery part](#step-e--build-the-battery-part)
10. [Step F – Battery meter (optional)](#step-f--battery-meter-optional)
11. [Step G – Beeper (optional)](#step-g--beeper-optional)
12. [Step H – Final check and put it in a box](#step-h--final-check-and-put-it-in-a-box)
13. [How to use it](#how-to-use-it)
14. [Make it personal](#make-it-personal)
15. [Something is wrong? (fixes)](#something-is-wrong-fixes)
16. [What each file does](#what-each-file-does)

---

## 1. What the gadget does

| Button | What happens when you tap it |
|---|---|
| **Kudos!** | A random nice message for the teacher, with a heart and confetti. |
| **Pomodoro** | A focus timer: 25 min work, 5 min break, and a 15 min break after 4 rounds. |
| **Quotes** | Inspiring quotes about learning. |
| **Fun Fact** | Random fun facts. |
| **Breaks** | Ideas for a 1-minute break. |
| **Thank You** | Your personal thank-you letter, page by page. |
| **Class Kit** | Coin flip, dice roll and a "pick a number" tool for picking students. |
| **Settings** | Brightness, battery level, and who made it. |

The screen dims by itself after 1 minute and turns off after 5 minutes. Tap it once to wake it up.

---

## 2. Shopping list

Tick each box when you have it.

- [ ] **1 × ESP32 dev board** (the common "ESP32 DevKit V1", 30 or 38 pins, with a USB port)
- [ ] **1 × 2.4" ILI9341 SPI touch screen** (the red board with **14 pins** in one row, labelled `VCC GND CS RESET DC SDI(MOSI) SCK LED SDO(MISO) T_CLK T_CS T_DIN T_DO T_IRQ`)
- [ ] **1 × 3.7 V LiPo battery** (1000 mAh or bigger is nice) with 2 wires (red and black)
- [ ] **1 × TP4056 charger board, the version WITH protection.** It has **6 pads**: `IN+  IN-  B+  B-  OUT+  OUT-`.
      The tiny 4-pad version has no protection, so **don't** buy that one.
- [ ] **1 × 3.3 V regulator chip "MCP1700-3302E"** (TO-92, looks like a tiny black half-moon with 3 legs). **HT7333-A** works too.
- [ ] **2 × 10 µF capacitors** (small electrolytic "cans", 16 V or more)
- [ ] **1 × small slide switch** (on/off)
- [ ] **2 × 100 kΩ resistors** (colour bands brown-black-yellow), only needed for the battery meter
- [ ] **Jumper wires, female-to-female**, about 20 (for testing before soldering)
- [ ] **Thin wire** for soldering (22–26 AWG), red and black plus another colour
- [ ] **Heat-shrink tube** or electrical tape
- [ ] **(Optional)** 1 × small **active buzzer** (5 V or 3 V) so the timer can beep
- [ ] **(Optional)** a small box, 3D-printed case or wooden frame
- [ ] **1 × USB cable** that fits your ESP32. It must be a **data** cable, not a "charge only" cable.

## 3. Tools you need

- Soldering iron and solder
- Wire cutter / stripper
- A multimeter (to check voltages, it's cheap and saves mistakes)
- A computer with the free program **Thonny** (https://thonny.org)

## 4. Safety first

- 🔥 The soldering iron is **very hot**. Always put it back in its stand.
- 🔋 **Never** let the red and black battery wires touch each other. That's a short circuit and it can get hot or catch fire.
- 🔋 Never poke, bend hard, or puncture the LiPo battery. If it ever gets puffy, stop using it.
- 🔌 **Rule for later:** when the ESP32's USB cable is plugged into the computer, the **slide switch must be OFF**.
- 👀 Do the soldering somewhere with fresh air.
- If you are young, ask a grown-up to help with the soldering and the battery.

---

## Step A – Put the program on the ESP32 (no soldering yet)

We do this first so we know the ESP32 works.

1. Download this project: on the GitHub page click the green **Code** button → **Download ZIP**. Unzip it.
2. Install **Thonny** on your computer and open it.
3. Plug the **ESP32** into the computer with the USB cable. Nothing else is connected yet.
4. In Thonny click **Tools → Options → Interpreter**.
5. Choose **"MicroPython (ESP32)"**.
6. Click **"Install or update MicroPython (esptool)"** (bottom right).
7. Pick your USB port, choose family **ESP32**, variant **Espressif • ESP32 / WROOM**, then click **Install**.
   - If it gets stuck on "Connecting…", **hold the BOOT button** on the ESP32 until it starts.
8. Wait until it says **Done**, then close the windows and click **OK**.
9. At the bottom of Thonny (the "Shell") you should see `>>>`. 🎉 The ESP32 is alive.
10. Click **View → Files**. You now see your computer's files at the top and the ESP32 ("MicroPython device") at the bottom.
11. On the top side, go into the unzipped project folder.
12. Right-click each of these files and choose **"Upload to /"**:
    - `main.py`
    - `config.py`
    - `content.py`
    - `calibrate.py`
13. On the bottom (ESP32) side, right-click → **New directory** → type `lib`.
14. Double-click the new `lib` folder on the ESP32 side to go inside it.
15. On the top side, open the project's `lib` folder. Right-click `ili9341.py` → **Upload to /lib**, then do the same for `xpt2046.py`.
16. Unplug the USB cable.

---

## Step B – Connect the screen

First we use **jumper wires** (no soldering) to test. We solder later, once everything works.

The ESP32's pins have names printed next to them, like `D15` or `GPIO15` or just `15`.
They all mean the same thing: pin **15**.

Look at the back of the screen. Find the row of 14 pins. Connect **one wire at a time** and tick it off:

| ✔ | Screen pin | goes to ESP32 pin | Wire colour idea |
|---|---|---|---|
| [ ] | `VCC` | `3V3` | red |
| [ ] | `GND` | `GND` | black |
| [ ] | `CS` | `15` (D15) | any |
| [ ] | `RESET` | `4` (D4) | any |
| [ ] | `DC` | `2` (D2) | any |
| [ ] | `SDI(MOSI)` | `23` (D23) | any |
| [ ] | `SCK` | `18` (D18) | any |
| [ ] | `LED` | `21` (D21) | any |
| [ ] | `SDO(MISO)` | `19` (D19) | any |
| [ ] | `T_CLK` | `25` (D25) | any |
| [ ] | `T_CS` | `33` (D33) | any |
| [ ] | `T_DIN` | `32` (D32) | any |
| [ ] | `T_DO` | `39` (VN) | any |
| [ ] | `T_IRQ` | `34` (D34) | any |

> 💡 Pin **39** is often labelled **VN** and pin **36** is labelled **VP**. Use **VN**.
> 💡 There may be 2 or 3 `GND` pins on the ESP32. Any of them is fine.
> 💡 Some screens also have 4 extra pins on the other end (`SD_...`). Those are for an SD card. Leave them empty.

Check every wire again against the table. A wrong wire is the #1 reason things don't work.

---

## Step C – Test it with USB power

1. Plug the ESP32 into the computer with USB.
2. The screen should light up and show a **pink heart** and **"For the BEST TEACHER"**.
3. Then the **menu** with 8 coloured buttons appears. 🎉

If the screen stays white or black, see [the fixes](#something-is-wrong-fixes).

Tapping might go to the wrong place right now. That's normal, and Step D fixes it.

---

## Step D – Make the touch work properly (calibrate)

1. Keep the ESP32 plugged in. Open **Thonny**.
2. Press the red **Stop** button so the menu program stops.
3. On the ESP32 side in Files, double-click **`calibrate.py`** to open it.
4. Press the green **Run** ▶ button.
5. A **red cross** appears in a corner. **Tap the middle of the cross** with your fingernail or a stylus.
6. Do the same for all **4 crosses**.
7. The Shell at the bottom prints some lines like:
   ```
   TOUCH_X_MIN = 230
   TOUCH_X_MAX = 3870
   ...
   ```
8. On the ESP32 side, double-click **`config.py`** to open it.
9. Find the lines starting with `TOUCH_X_MIN`, `TOUCH_X_MAX`, `TOUCH_Y_MIN`, `TOUCH_Y_MAX`, `TOUCH_INVERT_X`, `TOUCH_INVERT_Y`, and replace them with the numbers from step 7.
10. While you're in `config.py`, change `TEACHER_NAME` and `STUDENT_NAME` (see [Make it personal](#make-it-personal)).
11. Press **Ctrl+S** to save. Make sure it saves to the **MicroPython device**.
12. Press the **EN** (or **RST**) button on the ESP32. Now tapping a button opens the right screen. 🎉

---

## Step E – Build the battery part

Now we make it work **without** the USB cable.

### What we're building (the picture in words)

```
 BATTERY ──► TP4056 ──► SWITCH ──► 3.3V REGULATOR ──► ESP32 "3V3" pin
 (charges by plugging USB into the TP4056)
```

The battery gives 3.3 V to 4.2 V, which changes as it empties. The regulator makes a steady **3.3 V** for the ESP32.

### Get to know the regulator (MCP1700 / HT7333)

Hold it so the **flat side with the writing faces you** and the legs point **down**. From left to right, the legs are:

```
   ┌───────┐
   │ 1700  │   ← flat side facing you
   └┬──┬──┬┘
    │  │  │
   GND IN OUT
   (1) (2) (3)
```

> ⚠️ Check the datasheet of the exact chip you bought. Almost all MCP1700 and HT7333-A chips are GND-IN-OUT like this, but a few others are different.

### Get to know the capacitors

The capacitor has a **long leg (+)** and a **short leg (−)**. The side with the **stripe** is **−**.
Putting it in backwards can make it pop, so be careful.

### Solder it – one connection at a time

> ⚠️ **Do not plug in the battery until the last step of this part.**

1. **Look, but don't solder yet:** find pads **B+** and **B−** on the TP4056. The battery goes there, but **last** (step 6).
   Many batteries have a small white plug. If you cut it off later, cut **one wire at a time** so they never touch!

2. **TP4056 → switch**
   - [ ] Solder a red wire from TP4056 **OUT+** to the **middle leg** of the slide switch.
   - [ ] Solder another red wire to **one outer leg** of the switch. This is the "switched +" wire. Leave the third leg empty.

3. **Switch → regulator**
   - [ ] The "switched +" wire → regulator **IN** (middle leg).
   - [ ] TP4056 **OUT−** → black wire → regulator **GND** (left leg).

4. **Capacitors on the regulator** (they keep the power smooth)
   - [ ] Capacitor 1: **+ (long leg)** → regulator **IN**, **− (stripe)** → regulator **GND**
   - [ ] Capacitor 2: **+ (long leg)** → regulator **OUT**, **− (stripe)** → regulator **GND**

5. **Regulator → ESP32**
   - [ ] Regulator **OUT** (right leg) → red wire → ESP32 **3V3** pin
   - [ ] Regulator **GND** (left leg) → black wire → ESP32 **GND** pin
   - ⚠️ Use the **3V3** pin, **not** `VIN` or `5V`.

6. **Now the battery**
   - [ ] Make sure the **switch is OFF**.
   - [ ] Solder battery **red → B+**.
   - [ ] Solder battery **black → B−**.
   - [ ] Cover every bare solder joint with heat-shrink or tape.

### Test with the multimeter (2 minutes, very worth it)

1. Set the multimeter to **DC volts (V⎓), 20 V range**.
2. Unplug the ESP32 USB cable.
3. Turn the **switch ON**.
4. Put the **black probe on GND** and the **red probe on the ESP32 3V3 pin**.
5. You should read **about 3.3 V** (3.2–3.4 is fine).
   - ✅ About 3.3 V: great, the screen should light up and the gadget runs on battery! 🎉
   - ❌ 0 V: is the switch on? Is the battery charged? Check the wires again.
   - ❌ More than 3.6 V: **switch OFF right away.** The regulator is wired wrong or it's the wrong part.

### Charging

- Plug a USB cable into the **TP4056's** USB port (not the ESP32's).
- **Red** light = charging. **Blue/green** light = full.
- You can charge with the switch ON or OFF.

> 🔌 **Remember:** if you plug USB into the **ESP32** (to change the code), turn the **switch OFF** first.

---

## Step F – Battery meter (optional)

This makes the battery icon in the top-right corner show how full the battery is.

1. Twist the two **100 kΩ resistors** together end to end, so you get one long chain: `end A — resistor — middle — resistor — end B`.
2. [ ] Solder **end A** to the **"switched +"** wire (the switch leg that goes to the regulator IN).
3. [ ] Solder **end B** to **GND**.
4. [ ] Solder a wire from the **middle** (where the two resistors meet) to ESP32 pin **35** (D35).
5. Done. If you skip this step, open `config.py` and set `BATTERY_ADC_PIN = None`. The icon will show a `?`.

---

## Step G – Beeper (optional)

Makes a beep when a Pomodoro timer ends.

1. [ ] Buzzer **+** (long leg, or red wire) → ESP32 pin **26** (D26)
2. [ ] Buzzer **−** → ESP32 **GND**
3. Open `config.py` and change `BUZZER_PIN = None` to `BUZZER_PIN = 26`. Save.

---

## Step H – Final check and put it in a box

1. When everything works with jumper wires, **solder the screen wires** one at a time. Use the table in Step B again and tick each wire off.
2. Turn it on and tap every button once to check it.
3. Put it in a case. Leave holes for:
   - the screen,
   - the **slide switch**,
   - the **TP4056 USB port** (for charging).
4. Fix the battery with double-sided tape so it can't move. Keep it away from sharp things and the hot regulator.
5. Wrap it up and give it to your teacher! 🎁

---

## How to use it

- **Turn on:** slide the switch ON.
- **Turn off:** slide the switch OFF (do this at night to save battery).
- **Tap a button** to open it. Tap **`<`** in the top-left corner to go back.
- **Screen went dark?** Tap once to wake it up.
- **Pomodoro:** tap **Start**. You can leave and use other buttons. A small timer shows in the top bar. The screen flashes when time is up.
- **Charge:** plug USB into the charger board's port.

---

## Make it personal

All the words live in two files. You can change them on the ESP32 with Thonny (open → edit → Ctrl+S → press EN to restart).

- `config.py`
  - `TEACHER_NAME = "Ms. Lopez"`, with your teacher's name between the quotes
  - `STUDENT_NAME = "Kevin"`, with your name
  - The Pomodoro times (`POMO_WORK`, `POMO_SHORT`, `POMO_LONG`) are in minutes
- `content.py`
  - `COMPLIMENTS`: add your own nice messages
  - `THANK_YOU_PAGES`: **write your own letter here**, it's the best part!
  - `QUOTES`, `FUN_FACTS`, `BREAK_IDEAS`: change anything

Rules for the text: keep each message inside `"quotes"` with a comma after it, and only use normal keyboard letters. Emoji and accents (é, ñ) don't show on the screen.

---

## Something is wrong? (fixes)

| Problem | Try this |
|---|---|
| Screen is **white** | A wire is wrong or loose. Check `CS`, `DC`, `RESET`, `SCK`, `SDI` against the table. |
| Screen is **black** | Check the `LED` wire (pin 21). Is it powered? On some screens you must short the little pad marked **J1** on the back with a blob of solder when using 3.3 V. |
| Picture is **upside-down or mirrored** | In `config.py` change `TFT_MADCTL = 0x28` to `0xE8`. If still wrong, try `0x68` or `0xA8`. |
| **Red and blue swapped** | Change `TFT_MADCTL` from `0x28` to `0x20`. |
| Picture has **glitches / stripes** | Use shorter wires, or in `config.py` change `TFT_BAUD = 40_000_000` to `20_000_000`. |
| **Taps go to the wrong place** | Do Step D again. |
| **Touch does nothing** | Check the 5 `T_` wires. `T_DO` goes to **39 / VN**. |
| Thonny can't find the ESP32 | Try a different USB cable (some only charge). Install the "CP210x" or "CH340" USB driver for your board. |
| Works on USB, **not on battery** | Do the multimeter test in Step E. Charge the battery. Is the switch ON? |
| Battery icon shows `?` | The battery meter isn't wired (Step F), or `BATTERY_ADC_PIN = None`. |
| ESP32 keeps **restarting** on battery | The battery is low (charge it), or the capacitors on the regulator are missing. |

---

## What each file does

```
main.py        the gadget program (starts by itself when it's turned on)
config.py      pins, names, timer lengths, touch calibration numbers
content.py     all the words: compliments, quotes, facts, break ideas, letter
calibrate.py   run once to make touch accurate
lib/ili9341.py screen driver
lib/xpt2046.py touch driver
```

Made with ❤ by a grateful student.
