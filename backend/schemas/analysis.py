from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AdvisoryDetails(BaseModel):
    description: str
    symptoms: List[str]
    preventive_measures: List[str]
    management: List[str]


class PredictionResult(BaseModel):
    crop: str
    disease: str
    confidence: float
    status: str
    advisory: AdvisoryDetails


class AnalysisResponse(BaseModel):
    id: int
    user_id: int
    image_filename: str
    image_url: str
    crop: str
    disease: str
    confidence: float
    status: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    advisory: AdvisoryDetails
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    id: int
    image_filename: str
    image_url: str
    crop: str
    disease: str
    confidence: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_analyses: int
    diseases_detected: int
    healthy_results: int
    recent_analysis_at: Optional[datetime] = None
