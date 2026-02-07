#!/usr/bin/env python3
"""
Send weight from a load cell (HX711) on the Raspberry Pi to the Smart Meal backend.
Run this on the Pi while the Flask app runs on the same Pi (backend on Pi).

Wiring (typical):
  HX711 VCC -> 3.3V (or 5V), GND -> GND
  HX711 DT (data)  -> GPIO 5 (BCM)
  HX711 SCK (clock) -> GPIO 6 (BCM)
  Load cell: E+, E-, A+, A- to HX711 (check your load cell datasheet)

Calibration:
  1. Run with no weight on the scale, note raw value (tare).
  2. Put a known weight (e.g. 200g), note raw value.
  3. SCALE = (raw_with_weight - raw_tare) / known_weight_grams
  4. Set CALIBRATION_TARE and CALIBRATION_SCALE below or via env.

Install on Pi:
  pip install requests
  pip install RPi.GPIO
  pip install hx711   # or: pip install hx711-rpi-py (see alternate branch in script)
"""
import os
import time
import sys

# Where to send weight (backend on same Pi)
SERVER_URL = os.environ.get("SMART_MEAL_SERVER", "http://127.0.0.1:5000")

# GPIO (BCM numbering)
DATA_PIN = int(os.environ.get("HX711_DT", "5"))
CLOCK_PIN = int(os.environ.get("HX711_SCK", "6"))

# Calibration: raw reading at zero, and raw units per gram (adjust for your load cell)
CALIBRATION_TARE = float(os.environ.get("LOAD_CELL_TARE", "0"))
CALIBRATION_SCALE = float(os.environ.get("LOAD_CELL_SCALE", "-1"))  # e.g. -2100 raw per gram
SEND_INTERVAL = float(os.environ.get("LOAD_CELL_INTERVAL", "2.0"))

try:
    import requests
except ImportError:
    print("Install: pip install requests", file=sys.stderr)
    sys.exit(1)


def read_weight_grams():
    """Read weight from HX711 load cell. Returns grams, or None if no hardware."""
    try:
        # Try hx711 (mpibpc-mroose) – common on Pi
        from hx711 import HX711
        import RPi.GPIO as GPIO
        hx = HX711(dout_pin=DATA_PIN, pd_sck_pin=CLOCK_PIN)
        hx.reset()
        raw = hx.get_raw_data(3)
        GPIO.cleanup()
        if not raw:
            return None
        raw_avg = sum(raw) / len(raw)
        if CALIBRATION_SCALE == 0 or CALIBRATION_SCALE == -1:
            return 0.0
        grams = (raw_avg - CALIBRATION_TARE) / CALIBRATION_SCALE
        return round(max(0.0, grams), 1)
    except ImportError:
        try:
            # Try hx711_rpi_py (endail) – different API
            from hx711_rpi_py import HX711 as HX711_RPI
            hx = HX711_RPI(dout=DATA_PIN, pd_sck=CLOCK_PIN)
            raw = hx.read()
            if raw is None:
                return None
            grams = (raw - CALIBRATION_TARE) / CALIBRATION_SCALE if CALIBRATION_SCALE else 0
            return round(max(0.0, grams), 1)
        except ImportError:
            pass
    except Exception as e:
        print(f"HX711 read error: {e}", file=sys.stderr)
    return None


def send_weight(grams):
    url = f"{SERVER_URL.rstrip('/')}/api/sensor/weight"
    try:
        r = requests.post(url, json={"weight_g": grams}, timeout=3)
        return r.ok
    except Exception as e:
        print(f"POST failed: {e}", file=sys.stderr)
        return False


def main():
    print("Load cell → Smart Meal backend (same Pi)")
    print(f"Server: {SERVER_URL}  |  GPIO DT={DATA_PIN} SCK={CLOCK_PIN}")
    if CALIBRATION_SCALE == -1 or CALIBRATION_SCALE == 0:
        print("Using mock weight (set LOAD_CELL_SCALE and LOAD_CELL_TARE to calibrate)")
    print("Ctrl+C to stop.\n")

    while True:
        grams = read_weight_grams()
        if grams is None:
            grams = 250.0  # mock when no HX711
        if send_weight(grams):
            print(f"Sent {grams} g")
        time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
