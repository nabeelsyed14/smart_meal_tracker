import json

def load_nutrition_db():
    with open("C:/Users/nabee/PycharmProjects/smart_meal_system/nutrition/nutrition_db.json", "r") as f:
        return json.load(f)

if __name__ == "__main__":
    db = load_nutrition_db()
    print("Foods available:")
    for food in db:
        print("-", food)
