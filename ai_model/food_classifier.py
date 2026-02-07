import os

TF_AVAILABLE = False
TFLITE_AVAILABLE = False
TFLITE_MODEL_PATH = os.environ.get("FOOD_TFLITE_MODEL") or os.path.join(
    os.path.dirname(__file__), "food_model.tflite"
)

try:
    import tensorflow as tf
    import numpy as np
    from tensorflow.keras.applications.mobilenet_v2 import (
        MobileNetV2,
        preprocess_input,
        decode_predictions,
    )
    from tensorflow.keras.preprocessing import image
    TF_AVAILABLE = True
except ImportError:
    pass

try:
    import tflite_runtime.interpreter as tflite
    TFLITE_AVAILABLE = True
except ImportError:
    pass


def _classify_tflite(img_path):
    """Run TFLite model (e.g. on Pi). Expects model with ImageNet-style input 224x224, float."""
    if not os.path.isfile(TFLITE_MODEL_PATH):
        return None
    interp = tflite.Interpreter(model_path=TFLITE_MODEL_PATH)
    interp.allocate_tensors()
    input_idx = interp.get_input_details()[0]["index"]
    input_shape = interp.get_input_details()[0]["shape"]
    # Load and preprocess image to input_shape (e.g. [1, 224, 224, 3])
    try:
        from PIL import Image
        img = Image.open(img_path).resize((input_shape[1], input_shape[2]))
        import numpy as np
        x = np.array(img, dtype=np.float32) / 127.5 - 1.0
        if len(x.shape) == 2:
            x = np.stack([x] * 3, axis=-1)
        x = np.expand_dims(x, axis=0)
        interp.set_tensor(input_idx, x)
        interp.invoke()
        out = interp.get_tensor(interp.get_output_details()[0]["index"])
        # Simplified: return top class as (b'', 'label', prob). For full labels use a label file.
        idx = int(out[0].argmax())
        prob = float(out[0].max())
        return [("tflite", f"class_{idx}", prob)]
    except Exception:
        return None


def classify_food(img_path=None):
    if TFLITE_AVAILABLE:
        result = _classify_tflite(img_path)
        if result:
            return result
    if TF_AVAILABLE:
        import numpy as np
        from tensorflow.keras.applications.mobilenet_v2 import (
            MobileNetV2,
            preprocess_input,
            decode_predictions,
        )
        from tensorflow.keras.preprocessing import image
        model = MobileNetV2(weights="imagenet")
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = model.predict(x)
        return decode_predictions(preds, top=3)[0]
    return [("mock", "apple", 0.95)]


def get_food_label(results):
    for _, desc, prob in results:
        if prob > 0.5:
            return desc, prob
    return None, 0