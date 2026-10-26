import asyncio
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from fastapi.testclient import TestClient

from main import app
from services.sensor_service import SensorService, _normalize_payload, _is_stale, _parse_timestamp

client = TestClient(app)


def test_sensor_endpoints_offline():
    """
    When the physical sensor server is offline, endpoints must return
    clean status objects with HTTP 200 and safe messages without crashing.
    """
    # Temporarily point service to an offline port to verify resilience
    offline_service = SensorService(server_url="http://127.0.0.1:59999")
    with patch("api.sensor.sensor_service", offline_service):
        # 1. /sensor/status
        res_status = client.get("/sensor/status")
        assert res_status.status_code == 200
        data_status = res_status.json()
        assert "server_url" in data_status
        assert data_status["is_reachable"] is False
        assert data_status["has_data"] is False
        assert "Cannot connect" in data_status["message"] or "offline" in data_status["message"].lower()

        # 2. /sensor/latest
        res_latest = client.get("/sensor/latest")
        assert res_latest.status_code == 200
        data_latest = res_latest.json()
        assert data_latest["status"] == "offline"
        assert data_latest["is_demo"] is False
        assert data_latest["reading"] is None
    print("[OK] Offline resilience test passed cleanly.")


def test_sensor_sample_endpoint():
    """
    /sensor/sample loads historical CSV data and must be clearly tagged is_demo=True.
    """
    res = client.get("/sensor/sample")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "demo"
    assert data["is_demo"] is True
    assert data["reading"] is not None
    r = data["reading"]
    assert r["is_demo"] is True
    assert r["temp_avg"] is not None
    assert r["humidity_avg"] is not None
    assert r["ph"] is not None
    assert r["tds"] is not None
    assert r["ec"] is not None
    assert r["salinity"] is not None
    assert r["ldr1"] is not None
    assert r["ldr2"] is not None
    assert r["device_online"] is True
    print("\n[OK] Sample endpoint returned verified demo readings successfully.")


def test_payload_normalization_and_staleness():
    """
    Test normalization logic, missing field resilience, and staleness detection.
    """
    # 1. Fresh timestamp (e.g. 1 minute ago)
    recent_ts = (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
    raw_fresh = {
        "device_id": "TEST-PH",
        "timestamp": recent_ts,
        "temp_avg": 26.5,
        "temperature1": 26.0,
        "temperature2": 27.0,
        "humidity_avg": 65.2,
        "humidity1": 64.0,
        "humidity2": 66.4,
        "ph": 6.8,
        "tds": 450.0,
        "ec": 900.0,
        "salinity": 0.35,
        "ldr1": 4500.0,
        "ldr2": 4400.0,
        "device_online": True
    }
    reading_fresh = _normalize_payload(raw_fresh)
    assert reading_fresh.temp_avg == 26.5
    assert reading_fresh.is_stale is False
    assert reading_fresh.device_online is True

    # 2. Stale timestamp (2 hours ago)
    old_ts = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    raw_stale = dict(raw_fresh)
    raw_stale["timestamp"] = old_ts
    reading_stale = _normalize_payload(raw_stale)
    assert reading_stale.is_stale is True

    # 3. Missing/None fields resilience
    partial_raw = {
        "timestamp": recent_ts,
        "temp_avg": "invalid_num",
        "humidity_avg": None
    }
    reading_partial = _normalize_payload(partial_raw)
    assert reading_partial.temp_avg is None
    assert reading_partial.humidity_avg is None
    assert reading_partial.ph is None
    print("[OK] Payload normalization and staleness validation passed.")


@pytest.mark.asyncio
async def test_mocked_gateway_data_response():
    """
    Simulate HTTP response from hardware gateway GET /api/data on port 5000.
    """
    service = SensorService(server_url="http://mock-gateway:5000")

    mock_gateway_payload = {
        "status": "ok",
        "data": {
            "device_online": True,
            "temp_avg": 28.4,
            "temperature1": 28.6,
            "temperature2": 28.2,
            "humidity_avg": 75.5,
            "humidity1": 74.5,
            "humidity2": 76.5,
            "ph": 7.56,
            "tds": 18.1,
            "ec": 36.0,
            "salinity": 0.02,
            "ldr1": 0.087,
            "ldr2": 0.136
        }
    }

    class MockResponse:
        status_code = 200
        def json(self):
            return mock_gateway_payload

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MockResponse()

        # Test get_status
        status_resp = await service.get_status()
        assert status_resp.is_reachable is True
        assert status_resp.has_data is True
        assert status_resp.device_online is True

        # Test get_latest_reading
        latest_resp = await service.get_latest_reading()
        assert latest_resp.status == "connected"
        assert latest_resp.reading is not None
        assert latest_resp.reading.temp_avg == 28.4
        assert latest_resp.reading.humidity_avg == 75.5
        assert latest_resp.reading.ph == 7.56
        assert latest_resp.reading.ec == 36.0
        print("[OK] Mocked gateway data (/api/data) response verified.")


@pytest.mark.asyncio
async def test_mocked_live_server_response():
    """
    Simulate HTTP response from cloud_server GET /api/status.
    """
    service = SensorService(server_url="http://mock-sensor-server:5000")
    
    mock_payload = {
        "status": "ok",
        "latest": {
            "device_id": "PH-LIVE-1",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temp_avg": 54.3,
            "temperature1": 54.2,
            "temperature2": 54.4,
            "humidity_avg": 29.1,
            "humidity1": 28.8,
            "humidity2": 29.3,
            "ph": 8.66,
            "tds": 632.2,
            "ec": 1255.7,
            "salinity": 0.62,
            "ldr1": 7277.19,
            "ldr2": 6666.96,
            "device_online": True
        },
        "current_commands": []
    }

    class MockResponse:
        def __init__(self, url):
            self.url = url
            # Return 404 on /api/data to test fallback to /api/status
            self.status_code = 404 if "/api/data" in url else 200

        def json(self):
            return mock_payload

    async def mock_fetch(url):
        return MockResponse(url)

    with patch("httpx.AsyncClient.get", side_effect=mock_fetch):
        # Test get_status
        status_resp = await service.get_status()
        assert status_resp.is_reachable is True
        assert status_resp.has_data is True
        assert status_resp.device_id == "PH-LIVE-1"
        assert status_resp.is_stale is False

        # Test get_latest_reading
        latest_resp = await service.get_latest_reading()
        assert latest_resp.status == "connected"
        assert latest_resp.reading is not None
        assert latest_resp.reading.temp_avg == 54.3
        assert latest_resp.reading.humidity_avg == 29.1
        assert latest_resp.reading.ph == 8.66
        assert latest_resp.reading.tds == 632.2
        assert latest_resp.reading.ec == 1255.7
        assert latest_resp.reading.salinity == 0.62
        assert latest_resp.reading.ldr1 == 7277.19
        assert latest_resp.reading.ldr2 == 6666.96
        assert latest_resp.reading.device_online is True
        print("[OK] Mocked cloud server (/api/status) fallback verified.")


if __name__ == "__main__":
    test_sensor_endpoints_offline()
    test_sensor_sample_endpoint()
    test_payload_normalization_and_staleness()
    asyncio.run(test_mocked_gateway_data_response())
    asyncio.run(test_mocked_live_server_response())
    print("\nALL SENSOR MODULE TESTS PASSED PERFECTLY!")
