from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database.connection import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_filename = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=False)
    crop = Column(String(100), nullable=False)
    disease = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # "Healthy" or "Disease Detected"

    # Optional environmental sensors (Phase 2 integration)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    soil_moisture = Column(Float, nullable=True)

    # Serialized JSON containing description, symptoms, preventive_measures, management
    advisory_data = Column(Text, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="analyses")

    def get_advisory(self) -> dict:
        try:
            return json.loads(self.advisory_data)
        except Exception:
            return {
                "description": "",
                "symptoms": [],
                "preventive_measures": [],
                "management": []
            }

    def set_advisory(self, data: dict):
        self.advisory_data = json.dumps(data)
