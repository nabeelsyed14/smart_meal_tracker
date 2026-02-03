from nutrition.load_db import load_nutrition_db
from fusion.calorie_calc import calculate_nutrition

db = load_nutrition_db()
result = calculate_nutrition("white_rice", 200, db)
print(result)
