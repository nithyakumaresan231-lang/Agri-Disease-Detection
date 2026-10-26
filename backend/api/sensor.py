from fastapi import APIRouter, Query, status
from schemas.sensor import SensorStatusResponse, SensorDataResponse
from services.sensor_service import sensor_service
from services.sensor_logger_service import sensor_logger

router = APIRouter(prefix="/sensor", tags=["IoT Sensor Monitoring"])


@router.get("/status", response_model=SensorStatusResponse)
async def get_sensor_status():
    """
    Checks if the physical sensor cloud server is reachable and whether
    telemetry data has been received.
    """
    return await sensor_service.get_status()


@router.get("/latest", response_model=SensorDataResponse)
async def get_latest_sensor_reading():
    """
    Retrieves the latest verified sensor telemetry from the active sensor server.
    Returns status='offline' gracefully if the sensor server cannot be reached.
    """
    return await sensor_service.get_latest_reading()


@router.get("/sample", response_model=SensorDataResponse)
def get_sample_sensor_reading():
    """
    Returns verified historical sample data from sensor_data.csv for demonstration
    and UI evaluation. Explicitly tagged as is_demo=True.
    """
    return sensor_service.get_sample_reading()


@router.get("/history")
def get_sensor_history(limit: int = Query(50, ge=1, le=500)):
    """
    Returns recent chronological live sensor readings logged to the local CSV file.
    Only contains verified live sensor server telemetry (no mock/demo data).
    """
    readings = sensor_logger.get_recent_readings(limit=limit)
    return {
        "status": "ok",
        "count": len(readings),
        "limit": limit,
        "readings": readings
    }
