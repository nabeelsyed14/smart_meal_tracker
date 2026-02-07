# Running the full backend on the Raspberry Pi

This guide describes running **everything on the Pi**: Flask web app, API, AI (imaging + food classification), and **load cell (HX711)** for weight. The web app and Android app then connect to the Pi’s IP to see the same data.

---

## Can you run it locally on the Pi? Do you need reductions?

**Yes, you can run the full program on the Pi.** With a few **recommended reductions**, it runs well on a Pi 4 (2GB+). On a Pi 3, use the lighter options below.

| Component        | Runs on Pi? | Recommendation |
|-----------------|-------------|----------------|
| Flask + API     | Yes         | No change. Use 1 worker if you use Gunicorn. |
| Nutrition DB    | Yes         | No change (small JSON). |
| Weight (load cell) | Yes      | Use `scripts/pi_load_cell.py` (HX711) sending to localhost. |
| Imaging (camera)| Yes         | Use `scripts/pi_camera_meal.py` or your own capture → POST to localhost. |
| **AI (food classification)** | Yes | **Use TFLite or mock.** Avoid full TensorFlow on Pi (slow, high RAM). |

**Reductions that matter:**

1. **AI:** Use **TensorFlow Lite** (or mock for testing) instead of full TensorFlow. Full Keras MobileNetV2 is slow and uses a lot of RAM on the Pi.
2. **Flask:** Run with `--host=0.0.0.0` so other devices can connect. For production, use Gunicorn with **1 worker** to save memory.
3. **Optional:** Resize camera images before sending to the classifier (e.g. 224×224) to keep inference fast—your current pipeline already uses a fixed input size.

No other code changes are required; the same repo runs on the Pi. Web and Android just point to the **Pi’s IP**.

---

## Architecture (all on Pi)

```
                    ┌─────────────────────────────────────────────────┐
                    │              Raspberry Pi                        │
                    │  ┌─────────────┐  ┌──────────────┐               │
  Load cell (HX711)──┼─► pi_load_cell.py ──► POST /api/sensor/weight   │
                    │  └─────────────┘  └──────┬───────┘               │
                    │                          │                        │
  Pi camera         │  ┌─────────────────────┐  │  ┌─────────────────┐   │
  (photo) ──────────┼─► pi_camera_meal.py   ──┼─►│  Flask app      │   │
                    │  └─────────────────────┘  │  │  (web + API)    │   │
                    │                           │  │  + AI (TFLite)  │   │
                    │                           │  └────────┬────────┘   │
                    │                           │           │            │
                    └───────────────────────────┼───────────┼───────────┘
                                                │           │
  Web browser (PC/phone) ────────────────────────┘           │
  Android app ──────────────────────────────────────────────┘
  Both use: http://<Pi-IP>:5000
```

- **Pi** runs: Flask (web + API), AI (TFLite or mock), and (optionally) Gunicorn.
- **Load cell** is read by `pi_load_cell.py` on the Pi; it POSTs weight to `http://127.0.0.1:5000/api/sensor/weight`.
- **Pi camera** is used by `pi_camera_meal.py` (or similar); it POSTs a photo to `http://127.0.0.1:5000/api/meal`; the Pi runs the classifier and updates meals.
- **Web app and Android app** both use `http://<Pi-IP>:5000` to see the same data (daily total, recent meals, last weight).

---

## Step-by-step: backend on Pi

### 1. Copy the project to the Pi

From your PC (replace with your Pi user and IP):

```bash
scp -r c:\Users\nabee\PycharmProjects\smart_meal_system pi@192.168.1.20:~/
```

Or use a USB drive / SMB and copy the folder to e.g. `/home/pi/smart_meal_system`.

### 2. On the Pi: venv and dependencies

```bash
cd ~/smart_meal_system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

For the **load cell** script (HX711) you need GPIO and an HX711 library:

```bash
pip install RPi.GPIO
pip install hx711
# or: pip install hx711-rpi-py
```

For **AI on Pi** (choose one):

- **Mock (no real AI):** do nothing; the app uses a fixed label.
- **TFLite (recommended):** `pip install tflite-runtime` and place your `.tflite` model at `ai_model/food_model.tflite` (or set `FOOD_TFLITE_MODEL`). See `ai_model/food_classifier.py`.
- **Full TensorFlow:** `pip install tensorflow` — works but slow and heavy on RAM.

### 3. Run the Flask app on the Pi

```bash
cd ~/smart_meal_system
source venv/bin/activate
cd web_app
python app.py
```

Or with Gunicorn (1 worker to save RAM):

```bash
pip install gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 app:app
```

Leave this running. The web UI and API are at `http://<Pi-IP>:5000`.

### 4. Run the load cell script (HX711) on the Pi

In a **second terminal** (or background):

```bash
cd ~/smart_meal_system
source venv/bin/activate
python scripts/pi_load_cell.py
```

- Sends weight to `http://127.0.0.1:5000/api/sensor/weight` every 2 seconds (configurable via `LOAD_CELL_INTERVAL`).
- **Wiring:** HX711 DT → GPIO 5 (BCM), SCK → GPIO 6 (BCM). Override with env: `HX711_DT`, `HX711_SCK`.
- **Calibration:** Set `LOAD_CELL_TARE` (raw value at zero weight) and `LOAD_CELL_SCALE` (raw units per gram). See `scripts/pi_load_cell.py` docstring.

### 5. (Optional) Pi camera – add meal by photo

In a third terminal or when needed:

```bash
cd ~/smart_meal_system && source venv/bin/activate
python scripts/pi_camera_meal.py --url http://127.0.0.1:5000
```

This captures a photo and POSTs it to the local backend; the Pi runs the AI and updates meals.

### 6. Open the web app and Android app

- **Web:** On any device on the same Wi‑Fi, open **http://\<Pi-IP\>:5000** (e.g. `http://192.168.1.20:5000`). Find Pi IP with `hostname -I` on the Pi.
- **Android:** In the Smart Meal app, set **Server URL** to **http://\<Pi-IP\>:5000** and tap **Refresh**. You’ll see the same daily total and data as the web app.

---

## Load cell (HX711) wiring and calibration

**Typical wiring:**

- HX711 **VCC** → 3.3 V (or 5 V), **GND** → GND  
- HX711 **DT** (data) → GPIO **5** (BCM)  
- HX711 **SCK** (clock) → GPIO **6** (BCM)  
- Load cell: E+, E-, A+, A- to HX711 (see your load cell datasheet)

**Calibration:**

1. Run `pi_load_cell.py` with no weight; note the raw value (or add a `print(raw_avg)` in the script).
2. Put a known weight (e.g. 200 g) on the scale; note the new raw value.
3. `SCALE = (raw_with_weight - raw_tare) / 200` (units per gram; often negative).
4. Set env vars and run:
   - `LOAD_CELL_TARE=<raw_tare> LOAD_CELL_SCALE=<scale> python scripts/pi_load_cell.py`
   - Or edit the defaults at the top of `scripts/pi_load_cell.py`.

---

## Summary

| Question | Answer |
|----------|--------|
| Can the program run locally on the Pi? | **Yes.** Flask, API, imaging, weight, and AI can all run on the Pi. |
| Do you need reductions? | **Yes, for AI:** use TFLite or mock; avoid full TensorFlow. Use 1 Gunicorn worker if you use it. |
| Load cell? | Use **`scripts/pi_load_cell.py`** (HX711); it POSTs weight to the backend on the same Pi. |
| Where do web and Android get data? | Both use **http://\<Pi-IP\>:5000**; they see the same data from the single backend on the Pi. |
