import tensorflow as tf
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
    decode_predictions
)
from tensorflow.keras.preprocessing import image

# Load pre-trained model
model = MobileNetV2(weights="imagenet")

def classify_food(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    preds = model.predict(x)
    decoded = decode_predictions(preds, top=3)[0]

    return decoded


if __name__ == "__main__":
    img_path = "test_images/apple.jpg"  # change this
    results = classify_food(img_path)

    for label, desc, prob in results:
        print(f"{desc}: {prob:.2f}")

from ai_model.label_map import LABEL_MAP

def get_food_label(results):
    for _, desc, prob in results:
        if desc in LABEL_MAP and prob > 0.2:
            return LABEL_MAP[desc], prob
    return None, 0
    food, confidence = get_food_label(results)

    if food:
        print("Detected food:", food)
        print("Confidence:", round(confidence, 2))
    else:
        print("Food not confidently detected")
