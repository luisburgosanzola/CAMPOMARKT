import os
import json
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from django.conf import settings

from ..models import Disease
MODEL_PATH = os.path.join(settings.BASE_DIR, "Ashly", "chatbot", "ml", "plant_disease_model.h5")
LABELS_PATH = os.path.join(settings.BASE_DIR, "Ashly", "chatbot", "ml", "labels.json")
IMG_SIZE = (224, 224)

_model = None
_labels = None


def _get_model_and_labels():
    global _model, _labels
    if _model is None:
        _model = load_model(MODEL_PATH)
    if _labels is None:
        with open(LABELS_PATH, "r", encoding="utf8") as f:
            _labels = json.load(f)
    return _model, _labels


def predict_disease(img_path: str, top_k: int = 3):
    model, labels = _get_model_and_labels()

    img = image.load_img(img_path, target_size=IMG_SIZE)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    preds = model.predict(img_array)[0]
    preds = np.array(preds)

    if preds.ndim == 0:
        preds = np.array([float(preds)])

    top_idx = preds.argsort()[-top_k:][::-1]

    results = []
    for idx in top_idx:
        idx = int(idx)
        label = labels[idx] if idx < len(labels) else "unknown"
        conf = float(preds[idx]) * 100.0

        search_name = label.replace("_", " ")
        disease = Disease.objects.filter(name__icontains=search_name).first()

        results.append({
            "label": label,
            "confidence": round(conf, 2),
            "disease": disease
        })

    return results
