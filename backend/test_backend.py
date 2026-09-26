import io
from fastapi.testclient import TestClient
from main import app
from database.connection import init_db

init_db()
client = TestClient(app)

def test_full_flow():
    print("1. Testing Registration...")
    reg_data = {
        "name": "Kavitha Farmer",
        "email": "kavitha@agri.org",
        "password": "FarmerPassword123!",
        "confirm_password": "FarmerPassword123!",
        "phone": "+91 9876543210",
        "location": "Coimbatore, Tamil Nadu"
    }
    r = client.post("/auth/register", json=reg_data)
    assert r.status_code in (201, 400), f"Register unexpected status: {r.status_code}, {r.text}"
    print("   Registration test passed.")

    print("2. Testing Login...")
    login_data = {
        "email": "kavitha@agri.org",
        "password": "FarmerPassword123!"
    }
    r = client.post("/auth/login", json=login_data)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    token_data = r.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Login test passed. Token received.")

    print("3. Testing /auth/me...")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    user_me = r.json()
    assert user_me["email"] == "kavitha@agri.org"
    print(f"   Logged in as: {user_me['name']}")

    print("4. Testing /predict with Mock Prediction...")
    # Create fake image bytes
    fake_img = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb")
    files = {"file": ("tomato_leaf_sample.jpg", fake_img, "image/jpeg")}
    r = client.post("/predict", headers=headers, files=files)
    assert r.status_code == 200, f"Predict failed: {r.status_code} {r.text}"
    analysis = r.json()
    analysis_id = analysis["id"]
    assert analysis["crop"] == "Tomato"
    assert analysis["disease"] == "Early Blight"
    assert analysis["confidence"] == 94.2
    assert len(analysis["advisory"]["preventive_measures"]) > 0
    print(f"   Prediction succeeded! Analysis ID: {analysis_id}, Crop: {analysis['crop']}, Disease: {analysis['disease']}")

    print("5. Testing /history...")
    r = client.get("/history", headers=headers)
    assert r.status_code == 200
    history = r.json()
    assert len(history) >= 1
    assert any(h["id"] == analysis_id for h in history)
    print(f"   History retrieved: {len(history)} items.")

    print("6. Testing /history/{id}...")
    r = client.get(f"/history/{analysis_id}", headers=headers)
    assert r.status_code == 200
    det = r.json()
    assert det["id"] == analysis_id
    print("   Detail retrieval passed.")

    print("7. Testing User Isolation (User B cannot see User A's data)...")
    user_b_reg = {
        "name": "Ramesh Farmer",
        "email": "ramesh@agri.org",
        "password": "SecretPassword123!",
        "confirm_password": "SecretPassword123!"
    }
    client.post("/auth/register", json=user_b_reg)
    r_b = client.post("/auth/login", json={"email": "ramesh@agri.org", "password": "SecretPassword123!"})
    token_b = r_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B checks history
    r_b_hist = client.get("/history", headers=headers_b)
    assert r_b_hist.status_code == 200
    b_history = r_b_hist.json()
    assert not any(h["id"] == analysis_id for h in b_history), "Isolation violation: User B saw User A's history!"

    # User B tries to directly access User A's analysis
    r_b_det = client.get(f"/history/{analysis_id}", headers=headers_b)
    assert r_b_det.status_code == 404, "Isolation violation: User B accessed User A's detail!"
    print("   User isolation verified successfully: User B cannot access User A's data.")

    print("8. Testing /profile and /stats...")
    r_stats = client.get("/stats", headers=headers)
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert stats["total_analyses"] >= 1
    print(f"   User A stats: Total={stats['total_analyses']}, Diseases={stats['diseases_detected']}")

    r_prof_update = client.put("/profile", headers=headers, json={"location": "Salem, Tamil Nadu"})
    assert r_prof_update.status_code == 200
    assert r_prof_update.json()["location"] == "Salem, Tamil Nadu"
    print("   Profile update succeeded.")

    print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_flow()
