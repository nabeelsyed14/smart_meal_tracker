
try:
    import tensorflow as tf
    import numpy as np
    from tensorflow.keras.applications.mobilenet_v2 import (
        MobileNetV2,
        preprocess_input,
        decode_predictions
    )
    from tensorflow.keras.preprocessing import image
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


def classify_food(img_path=None):
    if TF_AVAILABLE:
        # Real TensorFlow inference (only works on machine with TF)
        model = MobileNetV2(weights="imagenet")
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = model.predict(x)
        return decode_predictions(preds, top=3)[0]
    else:
        # Fallback for Pi
        return [("mock", "apple", 0.95)]


def get_food_label(results):
    for _, desc, prob in results:
        if prob > 0.5:
            return desc, prob
    return None, 0