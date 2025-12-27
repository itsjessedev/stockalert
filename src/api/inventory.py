"""Inventory API endpoints"""

from typing import List
from fastapi import APIRouter, HTTPException, Query
from ..models import Product, StockLevel
from ..services import MonitorService

router = APIRouter(prefix="/inventory", tags=["inventory"])
monitor_service = MonitorService()


@router.get("/stock-levels", response_model=List[StockLevel])
async def get_stock_levels(
    location_id: str = Query(..., description="Location ID to check"),
):
    """
    Get current stock levels for all products at a location

    Returns real-time stock levels with velocity calculations and reorder suggestions
    """
    try:
        stock_levels = monitor_service.check_stock_levels(location_id)
        return stock_levels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/low-stock", response_model=List[StockLevel])
async def get_low_stock_items(
    location_id: str = Query(..., description="Location ID to check"),
):
    """
    Get only items with low or critical stock levels

    Filters stock levels to show only items that need attention
    """
    try:
        stock_levels = monitor_service.check_stock_levels(location_id)
        # Filter to only low, critical, or out of stock items
        low_stock = [
            s
            for s in stock_levels
            if s["status"] in ["low", "critical", "out_of_stock"]
        ]
        return low_stock
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_inventory(
    location_id: str = Query(..., description="Location ID to sync"),
):
    """
    Manually trigger inventory sync from Square POS

    Forces a sync of inventory data from Square and updates local cache
    """
    try:
        stock_levels = monitor_service.check_stock_levels(location_id)
        return {
            "status": "success",
            "message": f"Synced {len(stock_levels)} products",
            "location_id": location_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_inventory_summary(
    location_id: str = Query(..., description="Location ID to check"),
):
    """
    Get inventory summary statistics

    Returns aggregate statistics about stock levels
    """
    try:
        stock_levels = monitor_service.check_stock_levels(location_id)

        # Calculate summary statistics
        total_products = len(stock_levels)
        healthy = sum(1 for s in stock_levels if s["status"] == "healthy")
        low = sum(1 for s in stock_levels if s["status"] == "low")
        critical = sum(1 for s in stock_levels if s["status"] == "critical")
        out_of_stock = sum(1 for s in stock_levels if s["status"] == "out_of_stock")

        return {
            "total_products": total_products,
            "healthy": healthy,
            "low_stock": low,
            "critical": critical,
            "out_of_stock": out_of_stock,
            "needs_attention": low + critical + out_of_stock,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
