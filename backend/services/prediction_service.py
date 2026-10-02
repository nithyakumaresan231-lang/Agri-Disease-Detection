from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

import cv2
import numpy as np
import joblib

from services.advisory_service import advisory_service


# ML model location
ML_DIR = Path(__file__).resolve().parent.parent / "ml"
MODEL_PATH = ML_DIR / "models" / "disease_model.pkl"
CLASSES_PATH = ML_DIR / "models" / "classes.pkl"


class BasePredictionService(ABC):

    @abstractmethod
    async def predict(
        self,
        image_bytes: bytes,
        filename: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        soil_moisture: Optional[float] = None
    ) -> Dict[str, Any]:
        pass


class MLPredictionService(BasePredictionService):

    def __init__(self):
        self.model = None
        self.classes = []

        try:
            self.model = joblib.load(MODEL_PATH)
            self.classes = joblib.load(CLASSES_PATH)

            print("[MLPredictionService] Random Forest model loaded successfully")
            print("[MLPredictionService] Classes:", self.classes)

        except Exception as e:
            print("[MLPredictionService] Model loading error:", e)

    def _get_backend_class(self, class_name):
        mapping = {
            "tomato early blight": "Tomato___Early_blight",
            "tomato late blight": "Tomato___Late_blight",
            "tomato healthy": "Tomato___healthy",
            "potato early blight": "Potato___Early_blight",
            "potato late blight": "Potato___Late_blight",
            "potato healthy": "Potato___healthy",
            "pepper bell bacterial spot": "Pepper,_bell___Bacterial_spot",
            "pepper bell healthy": "Pepper,_bell___healthy"
        }

        return mapping.get(class_name.lower(), class_name)

    async def predict(
        self,
        image_bytes: bytes,
        filename: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        soil_moisture: Optional[float] = None
    ) -> Dict[str, Any]:

        if self.model is None:
            return {
                "crop": "Unknown",
                "disease": "Model not loaded",
                "confidence": 0,
                "status": "Error",
                "advisory": {}
            }

        # Convert uploaded image to OpenCV image
        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return {
                "crop": "Unknown",
                "disease": "Invalid image",
                "confidence": 0,
                "status": "Error",
                "advisory": {}
            }

        # Same preprocessing used during training
        image = cv2.resize(image, (32, 32))
        image = image.flatten().reshape(1, -1)

        # Prediction
        prediction = self.model.predict(image)[0]
        probabilities = self.model.predict_proba(image)[0]

        class_name = self.classes[int(prediction)]
        confidence = float(probabilities[int(prediction)] * 100)

        # Convert class name to backend format
        backend_class = self._get_backend_class(class_name)

        # Get advisory
        adv = advisory_service.get_by_class(backend_class)

        if not adv:
            crop = class_name.split()[0].capitalize()

            if "healthy" in class_name.lower():
                disease = "Healthy"
            elif "early" in class_name.lower():
                disease = "Early Blight"
            elif "late" in class_name.lower():
                disease = "Late Blight"
            elif "bacterial" in class_name.lower():
                disease = "Bacterial Spot"
            else:
                disease = "Unknown"

            adv = advisory_service.get_fallback(crop, disease)

        is_healthy = adv.get("is_healthy", False)

        status = "Healthy" if is_healthy else "Disease Detected"

        return {
            "crop": adv.get("crop", class_name.split()[0].capitalize()),
            "disease": adv.get("disease", class_name),
            "confidence": round(confidence, 2),
            "status": status,
            "advisory": {
                "description": adv.get("description", ""),
                "symptoms": adv.get("symptoms", []),
                "preventive_measures": adv.get("preventive_measures", []),
                "management": adv.get("management", [])
            }
        }


# Use the real ML prediction service
_prediction_service_instance = MLPredictionService()


def get_prediction_service() -> BasePredictionService:
    return _prediction_service_instance