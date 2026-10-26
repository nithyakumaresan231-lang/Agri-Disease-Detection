import csv
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
import asyncio

from schemas.sensor import SensorReading
from services.sensor_logger_service import SensorLoggerService, CSV_HEADERS
from services.sensor_service import SensorService


class TestSensorLoggerService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "data" / "sensor_test.csv"
        self.logger = SensorLoggerService(csv_path=self.test_csv_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_and_header_creation(self):
        self.assertTrue(self.test_csv_path.exists())
        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, CSV_HEADERS)

    def test_log_valid_reading(self):
        reading = SensorReading(
            device_id="PH-1",
            timestamp="2026-10-26 20:30:00",
            temp_avg=28.4,
            temperature1=28.2,
            temperature2=28.6,
            humidity_avg=75.6,
            humidity1=75.0,
            humidity2=76.2,
            ph=7.56,
            tds=18.0,
            ec=36.0,
            salinity=0.02,
            ldr1=0.09,
            ldr2=0.14,
            device_online=True,
            is_stale=False,
            is_demo=False
        )
        logged = self.logger.log_reading(reading)
        self.assertTrue(logged)

        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["device_id"], "PH-1")
            self.assertEqual(row["temp_avg"], "28.4")
            self.assertEqual(row["humidity_avg"], "75.6")
            self.assertEqual(row["ph"], "7.56")
            self.assertEqual(row["soil_moisture"], "")
            self.assertEqual(row["soil_temperature"], "")
            self.assertEqual(row["data_source"], "live_gateway")

    def test_deduplication_prevents_duplicate_rows(self):
        reading = SensorReading(
            device_id="PH-1",
            timestamp="2026-10-26 20:30:00",
            temp_avg=28.4,
            temperature1=28.2,
            temperature2=28.6,
            humidity_avg=75.6,
            humidity1=75.0,
            humidity2=76.2,
            ph=7.56,
            tds=18.0,
            ec=36.0,
            salinity=0.02,
            ldr1=0.09,
            ldr2=0.14,
            device_online=True,
            is_stale=False,
            is_demo=False
        )
        first_res = self.logger.log_reading(reading)
        self.assertTrue(first_res)

        # Polling again immediately with identical telemetry
        second_res = self.logger.log_reading(reading)
        self.assertFalse(second_res)

        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)

    def test_new_values_trigger_new_row(self):
        reading1 = SensorReading(
            device_id="PH-1",
            timestamp="2026-10-26 20:30:00",
            temp_avg=28.4,
            humidity_avg=75.6,
            ph=7.56,
            is_stale=False,
            is_demo=False
        )
        self.assertTrue(self.logger.log_reading(reading1))

        # Second reading with updated temp_avg
        reading2 = SensorReading(
            device_id="PH-1",
            timestamp="2026-10-26 20:30:10",
            temp_avg=28.5,
            humidity_avg=75.6,
            ph=7.56,
            is_stale=False,
            is_demo=False
        )
        self.assertTrue(self.logger.log_reading(reading2))

        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["temp_avg"], "28.4")
            self.assertEqual(rows[1]["temp_avg"], "28.5")

    def test_demo_and_mock_data_rejected(self):
        demo_reading = SensorReading(
            device_id="DEMO-1",
            timestamp="2026-10-26 20:30:00",
            temp_avg=25.0,
            humidity_avg=60.0,
            is_stale=False,
            is_demo=True
        )
        self.assertFalse(self.logger.log_reading(demo_reading))

        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 0)

    def test_get_recent_readings_bounded(self):
        # Insert 10 distinct readings
        for i in range(10):
            r = SensorReading(
                device_id="PH-1",
                timestamp=f"2026-10-26 20:30:{i:02d}",
                temp_avg=20.0 + i,
                is_stale=False,
                is_demo=False
            )
            self.logger.log_reading(r)

        # Request last 3
        recent = self.logger.get_recent_readings(limit=3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0]["temp_avg"], "27.0")
        self.assertEqual(recent[1]["temp_avg"], "28.0")
        self.assertEqual(recent[2]["temp_avg"], "29.0")

    def test_multithreaded_concurrency(self):
        def worker(thread_id):
            for j in range(5):
                r = SensorReading(
                    device_id=f"DEV-{thread_id}",
                    timestamp=f"2026-10-26 20:{thread_id:02d}:{j:02d}",
                    temp_avg=20.0 + thread_id + (j * 0.1),
                    is_stale=False,
                    is_demo=False
                )
                self.logger.log_reading(r)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # 4 threads * 5 unique readings = 20 rows
            self.assertEqual(len(rows), 20)


if __name__ == "__main__":
    unittest.main()
