#!/usr/bin/env python3
"""
Send a photo from the Raspberry Pi camera to the Smart Meal API for food detection.
Uses the same POST /api/meal endpoint as the web and Android – Pi camera is
treated as default image source (same pipeline).

Usage:
  python pi_camera_meal.py [--weight 250]
  (Set SERVER_URL below or pass --url http://192.168.1.10:5000)

Requires on Pi: pip install requests
Camera: picamera2 (Pi 5 / Bookworm) or picamera (older), or use --file for testing.
"""
import argparse
import sys
from pathlib import Path

SERVER_URL = "http://192.168.1.10:5000"  # Your Flask server


def capture_image(save_path: str) -> bool:
    """Capture one frame to save_path. Returns True if successful."""
    try:
        try:
            from picamera2 import Picamera2
            cam = Picamera2()
            cam.configure(cam.create_preview_configuration(main={"size": (640, 480)}))
            cam.start()
            cam.capture_file(save_path)
            cam.stop()
            return True
        except ImportError:
            pass
        try:
            import picamera
            with picamera.PiCamera() as cam:
                cam.capture(save_path)
            return True
        except ImportError:
            pass
    except Exception as e:
        print(f"Camera error: {e}", file=sys.stderr)
    return False


def send_meal_with_image(server_base: str, image_path: str, weight_g: float | None) -> None:
    """POST image to /api/meal. Uses last sensor weight if weight_g is None."""
    url = f"{server_base.rstrip('/')}/api/meal"
    with open(image_path, "rb") as f:
        files = {"food_image": (Path(image_path).name, f, "image/jpeg")}
        data = {} if weight_g is None else {"weight_g": weight_g}
        try:
            import requests
            r = requests.post(url, files=files, data=data, timeout=30)
            if r.ok:
                d = r.json()
                print(f"Detected: {d.get('food', '?')} | {d.get('nutrition', {}).get('calories', 0)} kcal | daily total: {d.get('daily_total_calories', 0)}")
            else:
                print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        except Exception as e:
            print(f"Request failed: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Pi camera → Smart Meal API")
    ap.add_argument("--url", default=SERVER_URL, help="Base URL of Flask server")
    ap.add_argument("--weight", type=float, default=None, help="Weight in grams (optional; uses scale weight if set)")
    ap.add_argument("--file", default=None, help="Use this image file instead of camera (for testing)")
    args = ap.parse_args()

    image_path = args.file
    if not image_path:
        image_path = "/tmp/smart_meal_capture.jpg"
        if not capture_image(image_path):
            print("No camera or capture failed. Use --file /path/to/image.jpg for testing.", file=sys.stderr)
            sys.exit(1)

    send_meal_with_image(args.url, image_path, args.weight)


if __name__ == "__main__":
    main()
