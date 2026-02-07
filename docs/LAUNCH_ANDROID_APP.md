# How to launch the Smart Meal Android app

Follow these steps to build and run the Android app from this project on an emulator or a physical device.

---

## 1. Install Android Studio

1. Download **Android Studio** from [developer.android.com/studio](https://developer.android.com/studio).
2. Run the installer and complete the setup wizard.
3. When prompted, install the **Android SDK** and accept the default components (Android SDK Platform, SDK Build-Tools, etc.).

---

## 2. Open the project

1. Start **Android Studio**.
2. Click **File → Open** (or **Open** on the welcome screen).
3. Navigate to the **`android_app`** folder inside this project:
   - Full path example: `c:\Users\nabee\PycharmProjects\smart_meal_system\android_app`
4. Select the **`android_app`** folder and click **OK**.
5. If Android Studio asks to trust the project or sync Gradle, choose **Trust Project** and wait for **Gradle sync** to finish (first time can take a few minutes).

---

## 3. Set up an emulator or device

### Option A: Run on an emulator

1. In Android Studio, go to **Tools → Device Manager** (or the device icon in the toolbar).
2. Click **Create Device** and pick a phone (e.g. **Pixel 6**).
3. Choose a system image (e.g. **API 34**) and download it if needed, then **Finish**.
4. Start the emulator with the **Play** button next to the device.

### Option B: Run on a physical Android phone

1. On your phone: **Settings → About phone** → tap **Build number** 7 times to enable Developer options.
2. **Settings → Developer options** → turn on **USB debugging**.
3. Connect the phone to your PC with a USB cable.
4. On the phone, allow **USB debugging** when prompted.
5. In Android Studio, your device should appear in the device dropdown next to any emulators.

---

## 4. Launch the app

1. In the toolbar, open the **Run** dropdown and select your **emulator** or **physical device**.
2. Click the green **Run** (Play) button, or press **Shift+F10** (Windows/Linux) / **Control+R** (Mac).
3. Android Studio will build the app and install it on the selected device. The **Smart Meal** app should open automatically.

---

## 5. Connect the app to your backend

1. **If the backend runs on your PC:**
   - **Emulator:** In the app, leave the server URL as **`http://10.0.2.2:5000`** (this is your PC from the emulator).
   - **Physical device:** Replace with your PC’s IP and port, e.g. **`http://192.168.1.10:5000`**. Your phone and PC must be on the same Wi‑Fi. Find your PC’s IP with `ipconfig` (Windows) or `ifconfig` / `ip addr` (Mac/Linux).

2. **If the backend runs on a Raspberry Pi:**
   - Use the Pi’s IP and port, e.g. **`http://192.168.1.20:5000`**.

3. Tap **Refresh** in the app to load foods and the daily total. Then add meals as needed.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Install Android Studio |
| 2 | **File → Open** → select the **`android_app`** folder in this project |
| 3 | Create/start an emulator or connect a phone with USB debugging |
| 4 | Click **Run** (green Play) to build and launch the app |
| 5 | Set the server URL in the app and tap **Refresh** |

If Gradle sync fails, use **File → Invalidate Caches → Invalidate and Restart**. If the app fails to reach the server, check that the URL has `http://` and that the device and server are on the same network.
