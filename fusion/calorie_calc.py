def calculate_nutrition(food, weight, db):
    if food not in db:
        raise ValueError("Food not found in database")

    factor = weight / 100.0
    data = db[food]

    return {
        "calories": round(data["calories"] * factor, 2),
        "protein": round(data["protein"] * factor, 2),
        "carbs": round(data["carbs"] * factor, 2),
        "fat": round(data["fat"] * factor, 2)
    }
