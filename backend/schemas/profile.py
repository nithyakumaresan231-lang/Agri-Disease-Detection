from typing import Optional
from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=150)
