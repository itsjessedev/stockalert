"""Stock monitoring service"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import Product, Alert, AlertCreate, AlertType, AlertSeverity
from ..config import settings
from .square import SquareService
from .forecaster import ForecasterService

logger = logging.getLogger(__name__)


class MonitorService:
    """Service for monitoring stock levels and generating alerts"""

    def __init__(self):
        self.square_service = SquareService()
        self.forecaster = ForecasterService()
        self.low_threshold = settings.low_stock_threshold_percentage
        self.critical_threshold = settings.critical_stock_threshold_percentage

    def check_stock_levels(self, location_id: str) -> List[Dict[str, Any]]:
        """Check stock levels for all products at a location"""
        logger.info(f"Checking stock levels for location: {location_id}")

        # Get current inventory
        inventory = self.square_service.get_inventory_counts(location_id)
        catalog = self.square_service.get_catalog_items(location_id)

        # Get sales history for velocity calculations
        sales_history = self.square_service.get_sales_history(location_id, days=30)

        results = []
        for inv_item in inventory:
            catalog_item = next(
                (c for c in catalog if c["id"] == inv_item["catalog_object_id"]), None
            )

            if not catalog_item:
                continue

            # Calculate velocity
            velocity = self.forecaster.calculate_velocity(
                inv_item["catalog_object_id"], sales_history
            )

            # Determine stock status
            current_stock = int(inv_item["quantity"])
            max_stock = 100  # Default max, should be configurable per product
            stock_percentage = (current_stock / max_stock) * 100

            status = self._determine_status(stock_percentage, current_stock)

            # Calculate days until stockout
            days_until_stockout = None
            if velocity > 0:
                days_until_stockout = self.forecaster.calculate_days_until_stockout(
                    current_stock, velocity
                )

            # Calculate suggested reorder quantity
            suggested_reorder = self.forecaster.calculate_reorder_quantity(
                velocity, current_stock, max_stock
            )

            results.append(
                {
                    "product_id": inv_item["catalog_object_id"],
                    "product_name": catalog_item["name"],
                    "location_id": location_id,
                    "current_stock": current_stock,
                    "max_stock": max_stock,
                    "stock_percentage": stock_percentage,
                    "status": status,
                    "velocity": velocity,
                    "days_until_stockout": days_until_stockout,
                    "suggested_reorder_quantity": suggested_reorder,
                }
            )

        return results

    def generate_alerts(
        self, stock_levels: List[Dict[str, Any]]
    ) -> List[AlertCreate]:
        """Generate alerts based on stock levels"""
        alerts = []

        for stock in stock_levels:
            current_stock = stock["current_stock"]
            stock_percentage = stock["stock_percentage"]
            velocity = stock.get("velocity", 0)
            days_until_stockout = stock.get("days_until_stockout")

            # Out of stock alert
            if current_stock == 0:
                alerts.append(
                    AlertCreate(
                        product_id=stock["product_id"],
                        location_id=stock["location_id"],
                        alert_type=AlertType.OUT_OF_STOCK,
                        severity=AlertSeverity.CRITICAL,
                        message=f"{stock['product_name']} is OUT OF STOCK",
                        current_stock=current_stock,
                        suggested_action=f"URGENT: Reorder {stock.get('suggested_reorder_quantity', 'immediately')} units immediately",
                    )
                )

            # Critical stock alert
            elif stock_percentage <= self.critical_threshold:
                alerts.append(
                    AlertCreate(
                        product_id=stock["product_id"],
                        location_id=stock["location_id"],
                        alert_type=AlertType.CRITICAL_STOCK,
                        severity=AlertSeverity.CRITICAL,
                        message=f"{stock['product_name']} is at CRITICAL stock level ({current_stock} units, {stock_percentage:.1f}%)",
                        current_stock=current_stock,
                        suggested_action=f"Reorder {stock.get('suggested_reorder_quantity', 'ASAP')} units immediately",
                    )
                )

            # Low stock alert
            elif stock_percentage <= self.low_threshold:
                alerts.append(
                    AlertCreate(
                        product_id=stock["product_id"],
                        location_id=stock["location_id"],
                        alert_type=AlertType.LOW_STOCK,
                        severity=AlertSeverity.WARNING,
                        message=f"{stock['product_name']} is at LOW stock level ({current_stock} units, {stock_percentage:.1f}%)",
                        current_stock=current_stock,
                        suggested_action=f"Consider reordering {stock.get('suggested_reorder_quantity', 'soon')} units",
                    )
                )

            # Reorder suggestion based on velocity
            elif (
                days_until_stockout
                and days_until_stockout <= 7
                and stock.get("suggested_reorder_quantity", 0) > 0
            ):
                alerts.append(
                    AlertCreate(
                        product_id=stock["product_id"],
                        location_id=stock["location_id"],
                        alert_type=AlertType.REORDER_SUGGESTED,
                        severity=AlertSeverity.INFO,
                        message=f"{stock['product_name']} will run out in {days_until_stockout} days at current velocity",
                        current_stock=current_stock,
                        suggested_action=f"Reorder {stock['suggested_reorder_quantity']} units to maintain optimal stock",
                    )
                )

        return alerts

    def _determine_status(self, stock_percentage: float, current_stock: int) -> str:
        """Determine stock status based on percentage and count"""
        if current_stock == 0:
            return "out_of_stock"
        elif stock_percentage <= self.critical_threshold:
            return "critical"
        elif stock_percentage <= self.low_threshold:
            return "low"
        else:
            return "healthy"
