"""Location models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    """Base location model"""

    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    square_location_id: Optional[str] = None


class LocationCreate(LocationBase):
    """Location creation model"""

    pass


class Location(LocationBase):
    """Location model with metadata"""

    id: str
    active: bool = True
    created_at: datetime
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True
