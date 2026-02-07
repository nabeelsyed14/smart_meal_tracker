# Smart Meal System – IoT Architecture

This document describes how sensors and the Android app communicate with the web backend.

**If the backend runs entirely on a Raspberry Pi** (Flask + AI + load cell + camera), see **[BACKEND_ON_PI.md](BACKEND_ON_PI.md)** for setup and how web/Android connect to the Pi.

## Overview

```
┌─────────────────┐     POST /api/sensor/weight    ┌──────────────────────┐
│  IoT scale /    │ ─────────────────────────────► │  Flask web app      │
│  Raspberry Pi   │                                │  (host 0.0.0.0:5000) │
└─────────────────┘     POST /api/meal (image)     │  - Web UI            │
┌─────────────────┐     ◄─────────────────────────  │  - REST API          │
│  Pi camera      │  (food detection = same as     │  - Daily totals      │
│  (photo)        │   web / Android)               │  - Recent meals      │
└─────────────────┘                                └──────────────────────┘
┌─────────────────┐     GET/POST /api/*             
│  Android app    │ ◄────────────────────────────► 
│  (phone/tablet) │                                 
└─────────────────┘
```

- **Web UI**: Browser on same network for manual and photo-based logging.
- **IoT – weight**: Scale or Pi sends weight to `POST /api/sensor/weight`. The server uses this as the default weight when a meal is added without weight (web, Android, or Pi).
- **IoT – Pi camera**: Images from the Pi camera are sent to the **same** `POST /api/meal` endpoint (multipart with `food_image` or `image`). They are processed exactly like web or Android uploads: same food classifier, same nutrition/health logic. **Pi camera is a first-class image source**—no separate path; it uses the default pipeline.
- **Android app**: Same REST API to add meals (manual or photo), get daily summary, and list foods.

## REST API

Base URL: `http://<your-server-ip>:5000` (use your machine’s LAN IP when testing from phone or Pi).

### 1. Send weight from sensor (IoT)

**POST** `/api/sensor/weight`

Body (JSON):

```json
{ "weight_g": 250 }
```

or `{ "weight": 250 }`.

Response: `{ "ok": true, "weight_g": 250 }`

Use this from a Raspberry Pi, ESP32, or any device that can do HTTP (e.g. Python `requests`, Arduino with Ethernet/WiFi, etc.).

### 2. Get last sensor weight

**GET** `/api/sensor/weight`

Response: `{ "weight_g": 250 }` or `{ "weight_g": null }`.

### 3. Add a meal (Android / API clients)

**POST** `/api/meal`

**Option A – JSON (manual):**

```json
{
  "food_id": "grilled_chicken",
  "weight_g": 150
}
```

If `weight_g` is omitted and a sensor weight was sent earlier, the server uses that value.

**Option B – Multipart (photo – web, Android, or Pi camera):**

- `food_image` or `image`: image file (from upload, phone camera, or **Pi camera**).
- Optional: `weight_g`. If missing, last sensor weight (e.g. from scale) or 100 g is used.

All image sources use the same pipeline; Pi camera images are not treated differently and become the default input when you send them from the Pi.

Response (success): e.g.

```json
{
  "ok": true,
  "food": "Grilled Chicken",
  "food_id": "grilled_chicken",
  "weight_g": 150,
  "nutrition": { "calories": 247.5, "protein": 46.5, "carbs": 0, "fat": 5.4 },
  "health_score": 100,
  "daily_total_calories": 500
}
```

### 4. Get daily summary

**GET** `/api/daily`

Response: e.g.

```json
{
  "daily_total_calories": 500,
  "last_sensor_weight_g": 250,
  "recent_meals": [ ... ]
}
```

### 5. List foods

**GET** `/api/foods`

Response: `{ "foods": [ "apple", "banana", "bread", ... ] }`

Use this to populate dropdowns or pickers in the Android app.

## Example: Raspberry Pi sending weight

```python
# On the Pi (or any Python device with network)
import requests

url = "http://<SERVER_IP>:5000/api/sensor/weight"
# Read weight from scale (e.g. HX711 + load cell, or serial)
weight_grams = 250  # or read from sensor
requests.post(url, json={"weight_g": weight_grams})
```

Replace `<SERVER_IP>` with the computer running the Flask app (e.g. `192.168.1.10`).

## Pi camera: send image for food detection

Images from the Pi camera use the **same** `POST /api/meal` endpoint as the web and Android. The server runs the same food classifier and nutrition logic—Pi camera is just another client.

Typical flow:

1. Pi captures a photo (e.g. with `picamera2` or `libcamera`).
2. Pi sends `POST /api/meal` with the image as multipart `food_image` or `image`.
3. Optionally send weight in the same request (or rely on a previous `POST /api/sensor/weight` from the scale).

Example script: `scripts/pi_camera_meal.py` (capture + POST). The response contains detected food, nutrition, and updated daily total—same as when uploading from the website.

## Example: Android calling the API

- **Add meal (manual):** `POST /api/meal` with JSON `{"food_id": "apple", "weight_g": 120}`.
- **Add meal (photo):** `POST /api/meal` with multipart body, field name `food_image` or `image`.
- **Daily total:** `GET /api/daily`.
- **Food list:** `GET /api/foods`.

Use the same base URL (e.g. `http://192.168.1.10:5000`) and ensure the phone and server are on the same network (or expose the server via tunnel for remote access).

## Security notes (production)

- Run over HTTPS and use a proper WSGI server (e.g. Gunicorn) instead of Flask’s dev server.
- Add authentication (e.g. API key or JWT) for `/api/meal` and `/api/daily` if multiple users or devices share the system.
- Restrict CORS if needed; for same-LAN Android/IoT, you may allow your app’s origin.

## Data persistence

The app currently keeps daily total, last sensor weight, and recent meals in memory. After restart, values reset. For production, persist these in a database (e.g. SQLite, PostgreSQL) or Redis and optionally add a “day” or user identifier.
