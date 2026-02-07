import json
import os


def load_nutrition_db():
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "nutrition_db.json")
    with open(file_path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    db = load_nutrition_db()
    print("Foods available:")
    for food in db:
        print("-", food)
