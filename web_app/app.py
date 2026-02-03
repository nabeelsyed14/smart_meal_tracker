from flask import Flask, render_template, request

# Imports from project root packages
from nutrition.load_db import load_nutrition_db
from fusion.calorie_calc import calculate_nutrition
from health_score.score_logic import compute_health_score
from mock_inputs.fake_weights import get_weight  # <- singular
from ai_model.food_classifier import classify_food, get_food_label

app = Flask(__name__)

# Load nutrition database
db = load_nutrition_db()

# Keep track of daily calories
daily_total = 0

@app.route("/", methods=["GET", "POST"])
def index():
    global daily_total
    food_name = None
    nutrition = None
    score = None
    confidence = None
    weight = get_weight()  # Mocked weight

    if request.method == "POST":
        # Mock AI selection from form for testing
        food_name = request.form.get("food_select")
        confidence = 1.0  # mock confidence

        if food_name:
            nutrition = calculate_nutrition(food_name, weight, db)
            score = compute_health_score(nutrition)
            daily_total += nutrition["calories"]

    # Food options for testing dropdown
    food_options = list(db.keys())

    return render_template(
        "index.html",
        food_name=food_name,
        confidence=confidence,
        weight=weight,
        nutrition=nutrition,
        score=score,
        daily_total=daily_total,
        food_options=food_options
    )

if __name__ == "__main__":
    # Ensure running from project root
    app.run(debug=True)
