# web_app/app.py – Smart Meal System: Web + IoT API

import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from nutrition.load_db import load_nutrition_db
from ai_model.food_classifier import classify_food, get_food_label
from fusion.calorie_calc import calculate_nutrition
from health_score.score_logic import compute_health_score

app = Flask(__name__)

from analyze_image import register_analyze_image
register_analyze_image(app)
# Load nutrition database
db = load_nutrition_db()

# In-memory state (use Redis/DB in production)
daily_total = 0
last_sensor_weight_g = None   # last weight from IoT scale
recent_meals = []             # list of { food, weight_g, nutrition, score }

# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    global daily_total, recent_meals, last_sensor_weight_g
    message = ""
    food_name = None
    weight = None
    nutrition = None
    score = None
    detected_food = ""
    confidence = 0

    if request.method == "POST":
        # Prefer image if both submitted
        uploaded_file = request.files.get("food_image")
        has_image = uploaded_file and uploaded_file.filename

        # 1) Manual: food select + weight (use sensor weight as default if available)
        weight_g = None
        if not has_image:
            food_select = request.form.get("food_select")
            weight_str = request.form.get("weight")
            if weight_str and weight_str.strip():
                try:
                    weight_g = float(weight_str)
                except ValueError:
                    message = "Invalid weight."
            if weight_g is None and last_sensor_weight_g is not None:
                weight_g = last_sensor_weight_g

        if not has_image and request.form.get("food_select") and weight_g is not None and weight_g > 0:
            food_select = request.form.get("food_select")
            try:
                nutrition = calculate_nutrition(food_select, weight_g, db)
                score = compute_health_score(nutrition)
                daily_total += nutrition["calories"]
                food_name = food_select.replace("_", " ").title()
                weight = weight_g
                recent_meals.insert(0, {
                    "food": food_name,
                    "weight_g": weight_g,
                    "nutrition": nutrition,
                    "score": score,
                })
                recent_meals[:] = recent_meals[:20]
            except ValueError as e:
                message = str(e) or "Food not in database."

        # 2) Image upload (camera / photo)
        if has_image:
            img_path = f"temp_{uploaded_file.filename}"
            try:
                uploaded_file.save(img_path)
                results = classify_food(img_path)
                detected_food, confidence = get_food_label(results)
                if detected_food:
                    # Map classifier label to DB key (e.g. "apple" -> "apple")
                    food_id = detected_food.lower().replace(" ", "_")
                    if food_id not in db:
                        food_id = next((k for k in db if food_id in k or k in food_id), None)
                    if food_id:
                        weight_g = weight_g if weight_g is not None else (last_sensor_weight_g or 100.0)
                        nutrition = calculate_nutrition(food_id, weight_g, db)
                        score = compute_health_score(nutrition)
                        daily_total += nutrition["calories"]
                        food_name = food_id.replace("_", " ").title()
                        weight = weight_g
                        recent_meals.insert(0, {
                            "food": food_name,
                            "weight_g": weight_g,
                            "nutrition": nutrition,
                            "score": score,
                        })
                        recent_meals[:] = recent_meals[:20]
                    else:
                        message = "Food not in database."
            finally:
                if os.path.exists(img_path):
                    os.remove(img_path)

    food_options = sorted(db.keys())
    return render_template(
        "index.html",
        food_options=food_options,
        food_name=food_name,
        weight=weight,
        nutrition=nutrition,
        score=score,
        daily_total=daily_total,
        message=message,
        detected_food=detected_food,
        confidence=confidence,
        last_sensor_weight=last_sensor_weight_g,
        recent_meals=recent_meals[:5],
    )


# ---------------------------------------------------------------------------
# REST API for IoT devices and Android app
# ---------------------------------------------------------------------------

@app.route("/api/sensor/weight", methods=["POST"])
def api_sensor_weight():
    """IoT scale or device sends current weight (grams)."""
    global last_sensor_weight_g
    try:
        data = request.get_json(force=True, silent=True) or {}
        w = data.get("weight_g") or data.get("weight")
        if w is not None:
            last_sensor_weight_g = float(w)
            return jsonify({"ok": True, "weight_g": last_sensor_weight_g})
        return jsonify({"ok": False, "error": "Missing weight_g or weight"}), 400
    except (TypeError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/sensor/weight", methods=["GET"])
def api_sensor_weight_get():
    """Get last weight received from sensor (for UI)."""
    return jsonify({"weight_g": last_sensor_weight_g})


@app.route("/api/meal", methods=["POST"])
def api_meal():
    """Add a meal: JSON { food_id, weight_g } or multipart with food_image."""
    global daily_total, recent_meals
    food_name = None
    weight = None
    nutrition = None
    score = None

    # JSON body or form: food_id + weight_g
    data = request.get_json(silent=True) or {}
    food_id = (data.get("food_id") or data.get("food") or "").strip()
    weight_g = data.get("weight_g") or data.get("weight")
    # Multipart (e.g. Pi camera) can send weight_g as form field
    if weight_g is None and request.form:
        weight_g = request.form.get("weight_g") or request.form.get("weight")
    if weight_g is not None:
        try:
            weight_g = float(weight_g)
        except (TypeError, ValueError):
            weight_g = None

    # Optional: use last sensor weight, else default 100 g
    if weight_g is None and last_sensor_weight_g is not None:
        weight_g = last_sensor_weight_g
    if weight_g is None:
        weight_g = 100.0

    # Multipart: image upload
    if not food_id and request.files:
        f = request.files.get("food_image") or request.files.get("image")
        if f and f.filename:
            path = f"temp_api_{f.filename}"
            try:
                f.save(path)
                results = classify_food(path)
                detected, _ = get_food_label(results)
                if detected:
                    food_id = detected.lower().replace(" ", "_")
                    if food_id not in db:
                        food_id = next((k for k in db if food_id in k or k in food_id), None)
                if not weight_g:
                    weight_g = 100.0
            finally:
                if os.path.exists(path):
                    os.remove(path)

    if not food_id or food_id not in db:
        return jsonify({"ok": False, "error": "Unknown food_id or missing image"}), 400
    if not weight_g or weight_g <= 0:
        return jsonify({"ok": False, "error": "Invalid or missing weight_g"}), 400

    try:
        nutrition = calculate_nutrition(food_id, weight_g, db)
        score = compute_health_score(nutrition)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    daily_total += nutrition["calories"]
    food_name = food_id.replace("_", " ").title()
    recent_meals.insert(0, {
        "food": food_name,
        "weight_g": weight_g,
        "nutrition": nutrition,
        "score": score,
    })
    recent_meals[:] = recent_meals[:20]

    return jsonify({
        "ok": True,
        "food": food_name,
        "food_id": food_id,
        "weight_g": weight_g,
        "nutrition": nutrition,
        "health_score": score,
        "daily_total_calories": daily_total,
    })


@app.route("/api/daily", methods=["GET"])
def api_daily():
    """Get today's summary and recent meals."""
    return jsonify({
        "daily_total_calories": daily_total,
        "last_sensor_weight_g": last_sensor_weight_g,
        "recent_meals": recent_meals[:10],
    })


@app.route("/api/foods", methods=["GET"])
def api_foods():
    """List available foods for dropdowns / Android."""
    return jsonify({"foods": sorted(db.keys())})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
