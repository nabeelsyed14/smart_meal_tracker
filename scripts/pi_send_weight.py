#!/usr/bin/env python3
"""
Example: send weight from Raspberry Pi (or any device) to the Smart Meal web app.
Replace SERVER_URL with your Flask server (e.g. http://192.168.1.10:5000).
Optionally read weight from a real sensor (e.g. HX711 + load cell) instead of mock.
"""
import sys
try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

SERVER_URL = "http://192.168.1.10:5000"  # Change to your server IP


def get_weight_grams():
    """Return weight in grams. Replace with real sensor read (e.g. HX711)."""
    # Mock: later replace with hardware read
    return 250


def main():
    weight = get_weight_grams()
    url = f"{SERVER_URL.rstrip('/')}/api/sensor/weight"
    try:
        r = requests.post(url, json={"weight_g": weight}, timeout=5)
        if r.ok:
            print(f"Sent weight: {weight} g")
        else:
            print(f"Server error: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    main()
