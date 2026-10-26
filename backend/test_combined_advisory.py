import io
import cv2
import numpy as np
from fastapi.testclient import TestClient

from main import app
from database.connection import init_db, SessionLocal
from models.user import User
from schemas.sensor import SensorReading
from services.auth_service import create_access_token, get_password_hash
from services.combined_advisory_service import generate_environmental_assessment, enrich_advisory

init_db()
client = TestClient(app)


def get_test_token():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_farmer@agri.org").first()
        if not user:
            user = User(
                name="Test Farmer",
                email="test_farmer@agri.org",
                password_hash=get_password_hash("Password123!")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return create_access_token({"sub": str(user.id), "email": user.email})
    finally:
        db.close()


def test_combined_advisory_without_sensor():
    """
    When no sensor readings exist, the advisory must remain 100% untouched.
    """
    base_advisory = {
        "description": "Standard foliar pathogen description.",
        "symptoms": ["Dark lesions on leaf surface"],
        "preventive_measures": ["Ensure plant spacing"],
        "management": ["Destroy infected foliage"]
    }

    enriched = enrich_advisory(
        base_advisory=base_advisory,
        crop="Tomato",
        disease="Late Blight",
        is_healthy=False,
        sensor_reading=None
    )

    assert enriched["description"] == base_advisory["description"]
    assert enriched["symptoms"] == base_advisory["symptoms"]
    assert enriched["preventive_measures"] == base_advisory["preventive_measures"]
    assert enriched["management"] == base_advisory["management"]
    assert enriched["environmental_assessment"] is None
    assert enriched["sensor_alerts"] == []
    assert enriched["data_source"] == "none"
    print("\n[OK] Combined advisory without sensor reading preserved base advisory identically.", flush=True)


def test_combined_advisory_with_high_humidity_and_blight():
    """
    When high humidity is detected, a specific microclimate alert must be added.
    """
    base_advisory = {
        "description": "Fungal foliar blight.",
        "symptoms": ["Water-soaked leaf lesions"],
        "preventive_measures": ["Use clean seed"],
        "management": ["Apply copper protective spray"]
    }

    sensor = SensorReading(
        device_id="PH-1",
        timestamp="2026-10-26 17:00:00",
        temp_avg=22.0,
        humidity_avg=88.5,
        ph=6.4,
        ec=1100.0,
        is_stale=False,
        is_demo=False
    )

    enriched = enrich_advisory(
        base_advisory=base_advisory,
        crop="Tomato",
        disease="Late Blight",
        is_healthy=False,
        sensor_reading=sensor
    )

    assert enriched["environmental_assessment"] is not None
    assert any("Humidity" in a for a in enriched["sensor_alerts"])
    assert any("[Environmental Advisory]" in m for m in enriched["management"])
    assert enriched["data_source"] == "live_gateway"
    print("[OK] Combined advisory with high humidity enriched with microclimate warning.", flush=True)


def test_combined_advisory_with_abnormal_ph():
    """
    When irrigation solution pH is acidic (<5.5), an irrigation alert is generated.
    """
    base_advisory = {
        "description": "Healthy foliage.",
        "symptoms": [],
        "preventive_measures": ["Maintain irrigation"],
        "management": []
    }

    sensor = SensorReading(
        device_id="PH-1",
        timestamp="2026-10-26 17:00:00",
        temp_avg=26.0,
        humidity_avg=55.0,
        ph=4.9,
        is_stale=False,
        is_demo=True
    )

    enriched = enrich_advisory(
        base_advisory=base_advisory,
        crop="Tomato",
        disease="Healthy",
        is_healthy=True,
        sensor_reading=sensor
    )

    assert any("pH" in a for a in enriched["sensor_alerts"])
    assert enriched["data_source"] == "demo_sample"
    print("[OK] Combined advisory detected abnormal pH solution correctly.", flush=True)


def test_predict_endpoint_with_sensor_form_fields():
    """
    Test POST /predict with form fields for temperature and humidity.
    """
    token = get_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Synthetic image
    valid_jpg = cv2.imencode('.jpg', np.zeros((100, 100, 3), dtype=np.uint8))[1].tobytes()
    files = {"file": ("leaf_test.jpg", io.BytesIO(valid_jpg), "image/jpeg")}
    data = {"temperature": "24.5", "humidity": "89.0"}

    res = client.post("/predict", headers=headers, files=files, data=data)
    assert res.status_code == 200, f"Predict failed: {res.text}"
    result = res.json()
    assert result["crop"] is not None
    assert result["disease"] is not None
    assert result["temperature"] == 24.5
    assert result["humidity"] == 89.0
    advisory = result["advisory"]
    assert advisory["environmental_assessment"] is not None
    assert len(advisory["sensor_alerts"]) > 0
    print(f"[OK] POST /predict succeeded with combined advisory.", flush=True)
    print(f"     Crop: {result['crop']}, Disease: {result['disease']}", flush=True)
    print(f"     Environmental Assessment: {advisory['environmental_assessment']}", flush=True)
    print(f"     Sensor Alerts: {advisory['sensor_alerts']}", flush=True)


if __name__ == "__main__":
    test_combined_advisory_without_sensor()
    test_combined_advisory_with_high_humidity_and_blight()
    test_combined_advisory_with_abnormal_ph()
    test_predict_endpoint_with_sensor_form_fields()
    print("\nALL COMBINED ADVISORY TESTS PASSED!", flush=True)
