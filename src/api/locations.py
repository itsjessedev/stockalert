"""Locations API endpoints"""

from typing import List
from fastapi import APIRouter, HTTPException
from ..models import Location
from datetime import datetime

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=List[Location])
async def get_locations():
    """
    Get all registered locations

    Returns list of all locations configured in the system
    """
    # In production, this would query a database
    # For demo, return mock locations
    return [
        Location(
            id="loc_001",
            name="Downtown Store",
            address="123 Main St",
            city="Seattle",
            state="WA",
            zip_code="98101",
            manager_name="Sarah Johnson",
            manager_phone="+1-206-555-0101",
            square_location_id="sq_loc_001",
            active=True,
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            last_sync=datetime.now(),
        ),
        Location(
            id="loc_002",
            name="Capitol Hill Store",
            address="456 Broadway Ave",
            city="Seattle",
            state="WA",
            zip_code="98102",
            manager_name="Mike Chen",
            manager_phone="+1-206-555-0102",
            square_location_id="sq_loc_002",
            active=True,
            created_at=datetime(2024, 1, 15, 0, 0, 0),
            last_sync=datetime.now(),
        ),
        Location(
            id="loc_003",
            name="Bellevue Store",
            address="789 NE 8th St",
            city="Bellevue",
            state="WA",
            zip_code="98004",
            manager_name="Emily Rodriguez",
            manager_phone="+1-425-555-0103",
            square_location_id="sq_loc_003",
            active=True,
            created_at=datetime(2024, 2, 1, 0, 0, 0),
            last_sync=datetime.now(),
        ),
    ]


@router.get("/{location_id}", response_model=Location)
async def get_location(location_id: str):
    """
    Get details for a specific location

    Returns detailed information about a single location
    """
    locations = await get_locations()
    location = next((loc for loc in locations if loc.id == location_id), None)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return location
