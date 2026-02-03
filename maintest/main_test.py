from nutrition.load_db import load_nutrition_db
from fusion.calorie_calc import calculate_nutrition
from health_score.score_logic import compute_health_score
from mock_inputs.fake_weights import get_weight

# Simulated AI output
food = "grilled_chicken"

db = load_nutrition_db()
weight = get_weight()

nutrition = calculate_nutrition(food, weight, db)
score = compute_health_score(nutrition)

print("Food:", food)
print("Weight:", weight, "g")
print("Nutrition:", nutrition)
print("Health Score:", score)
