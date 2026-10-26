import csv
from collections import deque
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
import threading
from typing import Optional, Dict, Any, List

from schemas.sensor import SensorReading

logger = logging.getLogger(__name__)

# Base directory: backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = BACKEND_DIR / "data" / "sensor_readings_live.csv"

# Minimum interval (seconds) before logging identical static values again as a heartbeat
HEARTBEAT_INTERVAL_SECONDS = 300

CSV_HEADERS = [
    "recorded_at",
    "sensor_timestamp",
    "device_id",
    "device_online",
    "temp_avg",
    "temperature1",
    "temperature2",
    "humidity_avg",
    "humidity1",
    "humidity2",
    "soil_moisture",
    "soil_temperature",
    "ph",
    "tds",
    "ec",
    "salinity",
    "ldr1",
    "ldr2",
    "data_source",
]


class SensorLoggerService:
    """
    Thread-safe, non-blocking CSV logging service for live IoT sensor readings.
    Automatically logs verified telemetry to backend/data/sensor_readings_live.csv.
    Prevents consecutive duplicate writes and rejects demo / mock data.
    """

    def __init__(self, csv_path: Path = DEFAULT_CSV_PATH):
        self.csv_path = Path(csv_path)
        self._lock = threading.Lock()
        self._last_fingerprint: Optional[str] = None
        self._last_logged_at: Optional[datetime] = None
        self._init_storage()

    def _init_storage(self) -> None:
        """
        Ensures the data directory and CSV header row exist.
        Initializes last fingerprint from the latest logged entry to prevent
        duplicates across server restarts.
        """
        try:
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
                with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(CSV_HEADERS)
            else:
                self._load_last_state()
        except Exception as e:
            logger.error(f"Failed to initialize sensor CSV logger at {self.csv_path}: {e}")

    def _compute_fingerprint(
        self,
        device_id: Optional[str],
        temp_avg: Optional[float],
        temp1: Optional[float],
        temp2: Optional[float],
        hum_avg: Optional[float],
        hum1: Optional[float],
        hum2: Optional[float],
        ph: Optional[float],
        tds: Optional[float],
        ec: Optional[float],
        salinity: Optional[float],
        ldr1: Optional[float],
        ldr2: Optional[float],
        device_online: Optional[bool] = None,
        raw_hardware_ts: Optional[str] = None,
    ) -> str:
        """
        Generates a composite MD5 hash fingerprint of physical measurements and device state.
        Only includes raw_hardware_ts if explicitly provided by the hardware device.
        """
        raw_sig = (
            f"{device_id}|{raw_hardware_ts or ''}|{device_online}|"
            f"{temp_avg}|{temp1}|{temp2}|"
            f"{hum_avg}|{hum1}|{hum2}|"
            f"{ph}|{tds}|{ec}|{salinity}|{ldr1}|{ldr2}"
        )
        return hashlib.md5(raw_sig.encode("utf-8")).hexdigest()

    def _load_last_state(self) -> None:
        """
        Reads the last valid row in the CSV to reconstruct the last known fingerprint
        and timestamp.
        """
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                last_row = None
                for row in reader:
                    last_row = row
                if last_row:
                    self._last_fingerprint = self._compute_fingerprint(
                        device_id=last_row.get("device_id"),
                        temp_avg=float(last_row["temp_avg"]) if last_row.get("temp_avg") else None,
                        temp1=float(last_row["temperature1"]) if last_row.get("temperature1") else None,
                        temp2=float(last_row["temperature2"]) if last_row.get("temperature2") else None,
                        hum_avg=float(last_row["humidity_avg"]) if last_row.get("humidity_avg") else None,
                        hum1=float(last_row["humidity1"]) if last_row.get("humidity1") else None,
                        hum2=float(last_row["humidity2"]) if last_row.get("humidity2") else None,
                        ph=float(last_row["ph"]) if last_row.get("ph") else None,
                        tds=float(last_row["tds"]) if last_row.get("tds") else None,
                        ec=float(last_row["ec"]) if last_row.get("ec") else None,
                        salinity=float(last_row["salinity"]) if last_row.get("salinity") else None,
                        ldr1=float(last_row["ldr1"]) if last_row.get("ldr1") else None,
                        ldr2=float(last_row["ldr2"]) if last_row.get("ldr2") else None,
                        device_online=last_row.get("device_online") == "True" if last_row.get("device_online") else None,
                        raw_hardware_ts=last_row.get("sensor_timestamp") or None,
                    )
                    rec_at_str = last_row.get("recorded_at")
                    if rec_at_str:
                        try:
                            self._last_logged_at = datetime.fromisoformat(rec_at_str)
                        except Exception:
                            self._last_logged_at = None
        except Exception as e:
            logger.warning(f"Could not load last fingerprint from CSV: {e}")

    def log_reading(
        self,
        reading: SensorReading,
        raw_payload: Optional[Dict[str, Any]] = None,
        data_source: str = "live_gateway",
    ) -> bool:
        """
        Appends a valid live sensor reading to the CSV file.
        Returns True if logged, False if skipped (duplicate, demo data, or write failure).
        """
        if not reading or reading.is_demo:
            return False

        try:
            # Check if raw hardware packet supplied an explicit timestamp
            raw_hardware_ts = None
            if raw_payload and isinstance(raw_payload, dict):
                raw_hardware_ts = (
                    raw_payload.get("timestamp") or
                    raw_payload.get("ts") or
                    raw_payload.get("created_at") or
                    raw_payload.get("time")
                )
                if raw_hardware_ts:
                    raw_hardware_ts = str(raw_hardware_ts).strip()

            fingerprint = self._compute_fingerprint(
                device_id=reading.device_id,
                temp_avg=reading.temp_avg,
                temp1=reading.temperature1,
                temp2=reading.temperature2,
                hum_avg=reading.humidity_avg,
                hum1=reading.humidity1,
                hum2=reading.humidity2,
                ph=reading.ph,
                tds=reading.tds,
                ec=reading.ec,
                salinity=reading.salinity,
                ldr1=reading.ldr1,
                ldr2=reading.ldr2,
                device_online=reading.device_online,
                raw_hardware_ts=raw_hardware_ts,
            )

            now_dt = datetime.now(timezone.utc)

            with self._lock:
                if fingerprint == self._last_fingerprint:
                    # Readings have not changed. Check heartbeat interval.
                    if self._last_logged_at:
                        diff_sec = abs((now_dt - self._last_logged_at).total_seconds())
                        if diff_sec < HEARTBEAT_INTERVAL_SECONDS:
                            # Skip consecutive polling duplicate
                            return False

                now_iso = now_dt.isoformat()

                # Extract soil fields if explicitly supplied in raw payload
                soil_moisture_val = ""
                soil_temp_val = ""
                if raw_payload and isinstance(raw_payload, dict):
                    sm = raw_payload.get("soil_moisture") or raw_payload.get("moisture")
                    st = raw_payload.get("soil_temperature") or raw_payload.get("soil_temp")
                    if sm is not None and str(sm).strip() != "":
                        soil_moisture_val = str(sm)
                    if st is not None and str(st).strip() != "":
                        soil_temp_val = str(st)

                # Original hardware timestamp if provided; else empty to avoid synthetic substitution
                sensor_ts_val = raw_hardware_ts if raw_hardware_ts else ""

                row = [
                    now_iso,
                    sensor_ts_val,
                    reading.device_id or "",
                    str(reading.device_online) if reading.device_online is not None else "",
                    str(reading.temp_avg) if reading.temp_avg is not None else "",
                    str(reading.temperature1) if reading.temperature1 is not None else "",
                    str(reading.temperature2) if reading.temperature2 is not None else "",
                    str(reading.humidity_avg) if reading.humidity_avg is not None else "",
                    str(reading.humidity1) if reading.humidity1 is not None else "",
                    str(reading.humidity2) if reading.humidity2 is not None else "",
                    soil_moisture_val,
                    soil_temp_val,
                    str(reading.ph) if reading.ph is not None else "",
                    str(reading.tds) if reading.tds is not None else "",
                    str(reading.ec) if reading.ec is not None else "",
                    str(reading.salinity) if reading.salinity is not None else "",
                    str(reading.ldr1) if reading.ldr1 is not None else "",
                    str(reading.ldr2) if reading.ldr2 is not None else "",
                    data_source,
                ]

                # Ensure file and header exist before appending
                if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
                    with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(CSV_HEADERS)

                with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
                    f.flush()

                self._last_fingerprint = fingerprint
                self._last_logged_at = now_dt
                return True
        except Exception as e:
            logger.error(f"Error logging sensor reading to CSV: {e}")
            return False

    def get_recent_readings(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves up to `limit` most recent readings chronologically from the CSV.
        Bounded memory usage using collections.deque.
        """
        if not self.csv_path.exists():
            return []

        limit = max(1, min(limit, 500))

        try:
            with self._lock:
                with open(self.csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    # Keep only the last `limit` rows in memory
                    tail_rows = deque(reader, maxlen=limit)
                    return list(tail_rows)
        except Exception as e:
            logger.error(f"Error reading sensor history from CSV: {e}")
            return []


# Singleton instance
sensor_logger = SensorLoggerService()
