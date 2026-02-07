# Smart Meal – Android App

This app talks to your Smart Meal Flask backend so you can log meals and see your daily total from your phone.

## Setup

1. Open the `android_app` folder in **Android Studio** (File → Open).
2. Sync Gradle and build.
3. Run on an emulator or a device on the **same Wi‑Fi** as the machine running the Flask server.

## Server URL

- **Emulator:** Keep `http://10.0.2.2:5000` (this is the host machine from the emulator).
- **Physical device:** Set the URL to your computer’s LAN IP and port, e.g. `http://192.168.1.10:5000`.

Find your PC’s IP: on Windows run `ipconfig`, on Mac/Linux run `ifconfig` or `ip addr`.

## Usage

1. Enter the **Server URL** and tap **Refresh** to load foods and daily total.
2. Choose a **food** from the list and optionally **weight (g)**. If you leave weight empty, the server uses the last value from the scale (if any) or 100 g.
3. Tap **Add Meal** to send the meal to the server. The daily total updates after a successful add.

## API used

- `GET /api/foods` – list of food IDs for the spinner
- `GET /api/daily` – daily total and recent meals
- `POST /api/meal` – body `{"food_id": "apple", "weight_g": 120}` (weight_g optional)

See the project’s `docs/IOT_ARCHITECTURE.md` for the full API and IoT integration.
