import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2

model = MobileNetV2(weights="imagenet")
print("Model loaded successfully")
