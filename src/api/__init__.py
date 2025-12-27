"""API endpoints"""

from .inventory import router as inventory_router
from .alerts import router as alerts_router
from .locations import router as locations_router

__all__ = ["inventory_router", "alerts_router", "locations_router"]
