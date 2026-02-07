# Running Smart Meal on Raspberry Pi (with AI locally)

You can run the full Python app on the Pi: **Flask web app + API + food classifier** all on the Pi. The website and API are then served from the Pi; the scale and Pi camera send data to the Pi itself.

**Running the full backend on the Pi (Flask + AI + load cell + camera), and connecting web + Android to the Pi:** see **[BACKEND_ON_PI.md](BACKEND_ON_PI.md)**.

## 1. Copy the project to the Pi

From your **PC** (PowerShell or terminal), with the Pi on the same network:

```bash
# Replace pi@192.168.1.20 with your Pi user and IP (find IP with your router or run 'hostname -I' on Pi)
scp -r c:\Users\nabee\PycharmProjects\smart_meal_system pi@192.168.1.20:~/
```

Or use **rsync** (if you have it) to sync only changed files:

```bash
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude 'android_app' c:\Users\nabee\PycharmProjects\smart_meal_system pi@192.168.1.20:~/
```

Or copy the folder via **USB drive** or **SMB share**: copy the whole `smart_meal_system` folder (you can omit `android_app` to save space) onto the Pi, e.g. into `/home/pi/smart_meal_system`.

## 2. On the Pi: open a terminal and go to the project

```bash
cd ~/smart_meal_system
```

(If you copied elsewhere, use that path.)

## 3. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate   # on Pi it's usually bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs **Flask** and **requests**. The app will run; for food **photo** detection you need one of the options below.

## 4. Running the AI locally on the Pi – three options

### Option A: Mock classifier (no AI, works immediately)

If you **do not** install TensorFlow, the app uses the **mock** classifier: it always returns a fixed label (e.g. "apple"). Good for testing the flow (scale, camera script, web UI) without heavy dependencies.

- **Do nothing extra** – the code already falls back to mock when TensorFlow is not available.

### Option B: Full TensorFlow on the Pi (real AI, but slow)

For **real** ImageNet-based classification on the Pi (slower, especially on Pi 3/4):

```bash
source ~/smart_meal_system/venv/bin/activate
pip install tensorflow
```

Then run the app (step 5). First request will download the model and may be slow; later inferences are faster but still heavier on the Pi. Prefer **Option C** for better performance.

### Option C: TensorFlow Lite on the Pi (recommended for local AI)

**The code is already set up for TFLite.** The classifier tries TFLite first when `tflite_runtime` is installed and a `.tflite` model file exists.

**On the Pi, after you `scp` the project:**

1. **Install TFLite runtime** (lightweight, no full TensorFlow):
   ```bash
   source ~/smart_meal_system/venv/bin/activate
   pip install tflite-runtime
   ```
   (On some Pi/OS combinations you may need a wheel from [TensorFlow Lite build](https://www.tensorflow.org/lite/guide/python). If `pip install tflite-runtime` fails, use the mock or full TensorFlow for now.)

2. **Add a TFLite model file** so the Pi can run real inference:
   - Either place your own **food model** as `ai_model/food_model.tflite`, or
   - Use an **ImageNet** MobileNet-style `.tflite` (224×224 input); the code maps common ImageNet classes to your nutrition DB (e.g. apple, banana, orange, pizza).
   - Optional: set a custom path with `export FOOD_TFLITE_MODEL=/path/to/model.tflite`.

3. **Run the app as usual** (step 5 below). Photo uploads and Pi camera images will use TFLite on the Pi. If no model file is present, the app falls back to mock or full TensorFlow.

Summary:

| Option | Install              | Speed on Pi | Use case              |
|--------|----------------------|------------|------------------------|
| A      | Nothing extra        | Instant    | Testing, no real AI    |
| B      | `pip install tensorflow` | Slow   | Real AI, no TFLite     |
| C      | `pip install tflite-runtime` + .tflite model | Fast | Real AI on Pi (recommended) |

## 5. Run the web app on the Pi

```bash
cd ~/smart_meal_system
source venv/bin/activate
cd web_app
python -m flask run --host=0.0.0.0 --port=5000
```

Or:

```bash
python app.py
```

Then from another device (phone, PC) on the same Wi‑Fi, open:

**http://\<Pi-IP\>:5000**

(e.g. `http://192.168.1.20:5000`). Find the Pi’s IP with `hostname -I` on the Pi.

## 6. Scale and camera scripts on the Pi

- **Scale:** Run `scripts/pi_send_weight.py` on the Pi (after setting `SERVER_URL` to `http://127.0.0.1:5000` or `http://localhost:5000` so it sends weight to the app on the same Pi).
- **Camera:** Run `scripts/pi_camera_meal.py` with `--url http://127.0.0.1:5000` so the photo is sent to the local Flask app; classification runs on the Pi (mock, TF, or TFLite depending on what you installed).

## 7. Run on boot (optional)

To start the web app automatically when the Pi boots (e.g. with systemd), create a service file; see your Pi’s documentation for “systemd service” or “run script on boot”.

---

**Summary:** Copy the project to the Pi → create venv → `pip install -r requirements.txt` → choose mock / TensorFlow / TFLite for local AI → run Flask from `web_app` with `--host=0.0.0.0`. Then use the website at `http://<Pi-IP>:5000` and point the scale/camera scripts to `http://127.0.0.1:5000`.
