"""Alert models"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AlertType(str, Enum):
    """Alert type enumeration"""

    LOW_STOCK = "low_stock"
    CRITICAL_STOCK = "critical_stock"
    OUT_OF_STOCK = "out_of_stock"
    REORDER_SUGGESTED = "reorder_suggested"
    VELOCITY_ANOMALY = "velocity_anomaly"


class AlertSeverity(str, Enum):
    """Alert severity enumeration"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertBase(BaseModel):
    """Base alert model"""

    product_id: str
    location_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    current_stock: int
    suggested_action: Optional[str] = None


class AlertCreate(AlertBase):
    """Alert creation model"""

    pass


class Alert(AlertBase):
    """Alert model with metadata"""

    id: str
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
