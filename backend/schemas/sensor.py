from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    device_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    # Ambient / Canopy Temperatures
    temp_avg: Optional[float] = None
    temperature1: Optional[float] = None
    temperature2: Optional[float] = None
    
    # Relative Humidity
    humidity_avg: Optional[float] = None
    humidity1: Optional[float] = None
    humidity2: Optional[float] = None
    
    # Water & Nutrient Solution Measurements
    ph: Optional[float] = None
    tds: Optional[float] = None
    ec: Optional[float] = None
    salinity: Optional[float] = None
    
    # Solar Radiation / Ambient Illumination
    ldr1: Optional[float] = None
    ldr2: Optional[float] = None
    
    # Device status
    device_online: Optional[bool] = None
    is_stale: bool = False
    is_demo: bool = False


class SensorStatusResponse(BaseModel):
    server_url: str
    is_reachable: bool
    has_data: bool
    device_id: Optional[str] = None
    device_online: Optional[bool] = None
    last_reading_time: Optional[str] = None
    is_stale: bool = False
    message: str


class SensorDataResponse(BaseModel):
    status: str  # "connected", "stale", "no_data", "offline", "demo"
    is_demo: bool = False
    server_url: str
    reading: Optional[SensorReading] = None
    raw_payload: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
