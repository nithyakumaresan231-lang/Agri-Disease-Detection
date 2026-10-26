import csv
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import httpx

from schemas.sensor import SensorReading, SensorStatusResponse, SensorDataResponse
from services.sensor_logger_service import sensor_logger

# Default to verified sensor server address requested by user
DEFAULT_SENSOR_SERVER_URL = "http://192.168.100.131:5000"
SENSOR_SERVER_URL = os.getenv("SENSOR_SERVER_URL", DEFAULT_SENSOR_SERVER_URL).rstrip("/")

# Historical sample CSV path for explicit demo mode
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLE_CSV_PATH = BASE_DIR / "sensor_integration_docs" / "sensor_data.csv"

# Staleness threshold in seconds (15 minutes)
STALE_THRESHOLD_SECONDS = 900


def _parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d-%m-%Y %H.%M",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(str(ts_str).strip(), fmt)
        except ValueError:
            continue
    return None


def _is_stale(dt: Optional[datetime]) -> bool:
    if not dt:
        return True
    
    # If dt has no timezone, assume local or UTC matching system
    now = datetime.now()
    diff = abs((now - dt).total_seconds())
    return diff > STALE_THRESHOLD_SECONDS


def _safe_float(val: Any) -> Optional[float]:
    if val is None or val == "" or str(val).lower() == "none":
        return None
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None


def _safe_bool(val: Any) -> Optional[bool]:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("true", "1", "t", "yes", "online"):
        return True
    if s in ("false", "0", "f", "no", "offline"):
        return False
    return None


def _normalize_payload(raw: Dict[str, Any]) -> SensorReading:
    """
    Extracts sensor fields whether they are passed flat or nested.
    """
    source = dict(raw)
    
    # If readings are nested inside 'readings' or 'sensors' or 'data', merge them
    for nested_key in ("readings", "sensors", "data"):
        if isinstance(source.get(nested_key), dict):
            for k, v in source[nested_key].items():
                source.setdefault(k, v)

    ts_raw = (
        source.get("timestamp") or
        source.get("ts") or
        source.get("time") or
        source.get("created_at") or
        source.get("last_updated")
    )
    dt = _parse_timestamp(str(ts_raw) if ts_raw else None)
    if dt:
        stale = _is_stale(dt)
        ts_str = str(ts_raw)
    elif source.get("device_online") is True or source.get("online") is True:
        # Live device actively streaming telemetry without explicit packet timestamp
        stale = False
        ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        stale = True
        ts_str = str(ts_raw) if ts_raw else None

    return SensorReading(
        device_id=str(source.get("device_id") or source.get("id") or "PH-1"),
        timestamp=ts_str,
        temp_avg=_safe_float(source.get("temp_avg") or source.get("temperature_avg") or source.get("temp")),
        temperature1=_safe_float(source.get("temperature1") or source.get("temp1")),
        temperature2=_safe_float(source.get("temperature2") or source.get("temp2")),
        humidity_avg=_safe_float(source.get("humidity_avg") or source.get("hum_avg") or source.get("humidity")),
        humidity1=_safe_float(source.get("humidity1") or source.get("hum1")),
        humidity2=_safe_float(source.get("humidity2") or source.get("hum2")),
        ph=_safe_float(source.get("ph")),
        tds=_safe_float(source.get("tds")),
        ec=_safe_float(source.get("ec")),
        salinity=_safe_float(source.get("salinity")),
        ldr1=_safe_float(source.get("ldr1")),
        ldr2=_safe_float(source.get("ldr2")),
        device_online=_safe_bool(source.get("device_online") or source.get("online")),
        is_stale=stale,
        is_demo=False
    )


class SensorService:
    def __init__(self, server_url: str = SENSOR_SERVER_URL):
        self.server_url = server_url

    async def _fetch_sensor_payload(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]], str]:
        """
        Queries the sensor server.
        1. First tries GET /api/data (served by gateway hardware on port 5000).
        2. Falls back to GET /api/status (served by cloud_server/server.py).

        Returns: (success: bool, raw_payload: Optional[dict], full_json: Optional[dict], message: str)
        """
        async with httpx.AsyncClient(timeout=3.0) as client:
            # 1. Try /api/data (Gateway controller endpoint)
            try:
                resp = await client.get(f"{self.server_url}/api/data")
                if resp.status_code == 200:
                    data = resp.json()
                    # Hardware gateway wraps active readings in data['data']
                    readings = data.get("data") if isinstance(data, dict) else None
                    if isinstance(readings, dict):
                        return True, readings, data, "Live sensor readings available from gateway"
            except (httpx.ConnectError, httpx.TimeoutException):
                raise
            except Exception:
                pass

            # 2. Try /api/status (Cloud server endpoint)
            try:
                resp = await client.get(f"{self.server_url}/api/status")
                if resp.status_code == 200:
                    data = resp.json()
                    readings = data.get("latest") if isinstance(data, dict) else None
                    if isinstance(readings, dict):
                        return True, readings, data, "Live sensor readings available from cloud server"
                    return True, None, data, "Connected to server, but no sensor telemetry received yet."
                return False, None, None, f"Sensor server returned HTTP {resp.status_code}"
            except (httpx.ConnectError, httpx.TimeoutException):
                raise
            except Exception as e:
                return False, None, None, f"Sensor communication error: {str(e)}"

    async def get_status(self) -> SensorStatusResponse:
        """
        Checks connectivity and telemetry availability on the sensor server.
        """
        try:
            has_data, latest, full_json, msg = await self._fetch_sensor_payload()
            if not has_data or not latest:
                return SensorStatusResponse(
                    server_url=self.server_url,
                    is_reachable=has_data,
                    has_data=False,
                    is_stale=True,
                    message=msg
                )

            normalized = _normalize_payload(latest)
            try:
                sensor_logger.log_reading(normalized, raw_payload=latest)
            except Exception:
                pass

            return SensorStatusResponse(
                server_url=self.server_url,
                is_reachable=True,
                has_data=True,
                device_id=normalized.device_id,
                device_online=normalized.device_online,
                last_reading_time=normalized.timestamp,
                is_stale=normalized.is_stale,
                message="Live sensor readings available" if not normalized.is_stale else "Latest sensor reading is stale"
            )
        except httpx.ConnectError:
            return SensorStatusResponse(
                server_url=self.server_url,
                is_reachable=False,
                has_data=False,
                is_stale=True,
                message=f"Cannot connect to sensor server at {self.server_url}. Server is offline or port is closed."
            )
        except httpx.TimeoutException:
            return SensorStatusResponse(
                server_url=self.server_url,
                is_reachable=False,
                has_data=False,
                is_stale=True,
                message=f"Connection timed out while contacting sensor server at {self.server_url}."
            )
        except Exception as e:
            return SensorStatusResponse(
                server_url=self.server_url,
                is_reachable=False,
                has_data=False,
                is_stale=True,
                message=f"Sensor communication error: {str(e)}"
            )

    async def get_latest_reading(self) -> SensorDataResponse:
        """
        Retrieves the latest validated sensor reading from the live sensor server.
        """
        try:
            has_data, latest, full_json, msg = await self._fetch_sensor_payload()
            if not has_data or not latest:
                return SensorDataResponse(
                    status="no_data" if has_data else "offline",
                    is_demo=False,
                    server_url=self.server_url,
                    message=msg
                )

            normalized = _normalize_payload(latest)
            status_str = "stale" if normalized.is_stale else "connected"

            try:
                sensor_logger.log_reading(normalized, raw_payload=latest)
            except Exception:
                pass

            return SensorDataResponse(
                status=status_str,
                is_demo=False,
                server_url=self.server_url,
                reading=normalized,
                raw_payload=latest,
                message="Live reading received" if status_str == "connected" else "Reading received but timestamp indicates data is stale"
            )
        except httpx.ConnectError:
            return SensorDataResponse(
                status="offline",
                is_demo=False,
                server_url=self.server_url,
                message=f"Cannot reach sensor server at {self.server_url}. Verify server is running on the configured host and port."
            )
        except httpx.TimeoutException:
            return SensorDataResponse(
                status="offline",
                is_demo=False,
                server_url=self.server_url,
                message=f"Connection timeout reaching sensor server at {self.server_url}."
            )
        except Exception as e:
            return SensorDataResponse(
                status="offline",
                is_demo=False,
                server_url=self.server_url,
                message=f"Sensor service error: {str(e)}"
            )

    def get_sample_reading(self) -> SensorDataResponse:
        """
        Loads the latest sample reading from historical CSV (sensor_data.csv).
        Explicitly marked with is_demo=True and status='demo'.
        """
        if not SAMPLE_CSV_PATH.exists():
            return SensorDataResponse(
                status="no_data",
                is_demo=True,
                server_url="local_sample_file",
                message="Sample sensor CSV file not found on disk."
            )

        try:
            with open(SAMPLE_CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows:
                    return SensorDataResponse(
                        status="no_data",
                        is_demo=True,
                        server_url="local_sample_file",
                        message="Sample sensor CSV is empty."
                    )
                
                # Pick the latest sample row
                last_row = rows[-1]
                normalized = _normalize_payload(last_row)
                normalized.is_demo = True
                normalized.is_stale = False  # Set to false for demo evaluation purposes

                return SensorDataResponse(
                    status="demo",
                    is_demo=True,
                    server_url="sensor_integration_docs/sensor_data.csv",
                    reading=normalized,
                    raw_payload=last_row,
                    message="Historical sample data loaded for interface demonstration (NOT LIVE SENSOR READINGS)."
                )
        except Exception as e:
            return SensorDataResponse(
                status="offline",
                is_demo=True,
                server_url="local_sample_file",
                message=f"Failed to read sample data: {str(e)}"
            )


# Singleton instance
sensor_service = SensorService()
