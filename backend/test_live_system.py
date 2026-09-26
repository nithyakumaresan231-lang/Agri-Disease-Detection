import io
import httpx as requests


BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== LIVE SYSTEM VERIFICATION ===")

    # 1. Health check
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    print("[OK] Health check OK:", r.json())

    # 2. Register User A
    user_a = {
        "name": "Arun Kumar",
        "email": "arun.farmer@agri.org",
        "password": "FarmerSecret123!",
        "confirm_password": "FarmerSecret123!",
        "phone": "+91 9444123456",
        "location": "Thanjavur, Tamil Nadu"
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=user_a)
    print("[OK] User A Registration status:", r.status_code)
    assert r.status_code in (201, 400) # 400 if already created in earlier run

    # 3. Login User A
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "arun.farmer@agri.org",
        "password": "FarmerSecret123!"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    token_a = r.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print("[OK] User A Login OK, JWT token issued.")

    # 4. Check /auth/me
    r = requests.get(f"{BASE_URL}/auth/me", headers=headers_a)
    assert r.status_code == 200
    print("[OK] User A Profile authenticated:", r.json()["name"])

    # 5. Prediction with synthetic leaf image
    # Minimal valid 1x1 JPEG bytes
    jpeg_bytes = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00"
        b"\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00"
        b"\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
    )
    files = {"file": ("tomato_leaf_test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}
    data = {"temperature": "28.5", "humidity": "75.0", "soil_moisture": "60.0"}
    r = requests.post(f"{BASE_URL}/predict", headers=headers_a, files=files, data=data)
    assert r.status_code == 200, f"Predict failed: {r.text}"
    analysis = r.json()
    analysis_id = analysis["id"]
    print(f"[OK] Prediction OK! ID={analysis_id}, Crop={analysis['crop']}, Disease={analysis['disease']}, Confidence={analysis['confidence']}%")
    assert analysis["crop"] == "Tomato"
    assert analysis["disease"] == "Early Blight"
    assert analysis["confidence"] == 94.2
    assert "image_url" in analysis
    assert len(analysis["advisory"]["preventive_measures"]) > 0

    # 6. Verify image access via static /uploads route
    img_url = f"{BASE_URL}{analysis['image_url']}"
    r_img = requests.get(img_url)
    assert r_img.status_code == 200, f"Uploaded image not accessible at {img_url}"
    print(f"[OK] Uploaded image served properly at {analysis['image_url']} (status: {r_img.status_code})")

    # 7. Check /history
    r = requests.get(f"{BASE_URL}/history", headers=headers_a)
    assert r.status_code == 200
    history = r.json()
    assert len(history) >= 1
    assert any(h["id"] == analysis_id for h in history)
    print(f"[OK] History verified: {len(history)} analyses recorded for User A.")

    # 8. Check /history/{id}
    r = requests.get(f"{BASE_URL}/history/{analysis_id}", headers=headers_a)
    assert r.status_code == 200
    assert r.json()["id"] == analysis_id
    print("[OK] History detail retrieval OK.")

    # 9. Test User Isolation with User B
    user_b = {
        "name": "Priya Selvam",
        "email": "priya.farmer@agri.org",
        "password": "PriyaSecret123!",
        "confirm_password": "PriyaSecret123!"
    }
    requests.post(f"{BASE_URL}/auth/register", json=user_b)
    r_b = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "priya.farmer@agri.org",
        "password": "PriyaSecret123!"
    })
    assert r_b.status_code == 200
    headers_b = {"Authorization": f"Bearer {r_b.json()['access_token']}"}

    # User B checks history (should NOT contain User A's analysis)
    r_b_hist = requests.get(f"{BASE_URL}/history", headers=headers_b)
    assert r_b_hist.status_code == 200
    assert not any(h["id"] == analysis_id for h in r_b_hist.json()), "ISOLATION ERROR: User B can see User A's history!"
    print("[OK] User isolation verified: User B cannot see User A's records in history.")

    # User B attempts to access User A's analysis directly by ID (must return 404)
    r_b_det = requests.get(f"{BASE_URL}/history/{analysis_id}", headers=headers_b)
    assert r_b_det.status_code == 404, f"ISOLATION ERROR: User B accessed User A's detail! Status: {r_b_det.status_code}"
    print("[OK] User isolation verified: User B gets 404 when querying User A's analysis ID.")

    # 10. Update Profile & Check Stats
    r_stats = requests.get(f"{BASE_URL}/stats", headers=headers_a)
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert stats["total_analyses"] >= 1
    print(f"[OK] Stats OK: Total={stats['total_analyses']}, Flagged={stats['diseases_detected']}")

    r_prof = requests.put(f"{BASE_URL}/profile", headers=headers_a, json={
        "location": "Madurai, Tamil Nadu"
    })
    assert r_prof.status_code == 200
    assert r_prof.json()["location"] == "Madurai, Tamil Nadu"
    print("[OK] Profile update OK.")

    print("\n[SUCCESS] ALL LIVE END-TO-END SYSTEM TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_tests()
