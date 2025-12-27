"""Inventory forecasting and velocity calculations"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class ForecasterService:
    """Service for calculating inventory velocity and reorder quantities"""

    def calculate_velocity(
        self, product_id: str, sales_history: List[Dict[str, Any]], days: int = 30
    ) -> float:
        """
        Calculate product velocity (units sold per day)

        Args:
            product_id: Product catalog ID
            sales_history: List of sales orders
            days: Number of days to analyze

        Returns:
            Average units sold per day
        """
        try:
            # Count total units sold for this product
            total_units = 0
            for order in sales_history:
                for line_item in order.get("line_items", []):
                    if line_item.get("catalog_object_id") == product_id:
                        quantity = float(line_item.get("quantity", 0))
                        total_units += quantity

            # Calculate average per day
            if days > 0:
                velocity = total_units / days
            else:
                velocity = 0

            logger.debug(
                f"Product {product_id}: {total_units} units sold in {days} days = {velocity:.2f} units/day"
            )
            return round(velocity, 2)

        except Exception as e:
            logger.error(f"Failed to calculate velocity for {product_id}: {str(e)}")
            return 0.0

    def calculate_days_until_stockout(
        self, current_stock: int, velocity: float
    ) -> Optional[int]:
        """
        Calculate days until product will run out of stock

        Args:
            current_stock: Current stock level
            velocity: Units sold per day

        Returns:
            Number of days until stockout, or None if velocity is 0
        """
        if velocity <= 0:
            return None

        days = current_stock / velocity
        return int(days)

    def calculate_reorder_quantity(
        self,
        velocity: float,
        current_stock: int,
        max_stock: int,
        lead_time_days: int = 7,
        safety_stock_days: int = 7,
    ) -> int:
        """
        Calculate suggested reorder quantity

        Args:
            velocity: Units sold per day
            current_stock: Current stock level
            max_stock: Maximum stock capacity
            lead_time_days: Days until reorder arrives
            safety_stock_days: Extra buffer days

        Returns:
            Suggested reorder quantity
        """
        if velocity <= 0:
            return 0

        # Calculate total days to cover (lead time + safety stock)
        total_days = lead_time_days + safety_stock_days

        # Calculate target stock level
        target_stock = velocity * total_days

        # Calculate how much to order
        reorder_quantity = target_stock - current_stock

        # Don't exceed max stock
        if current_stock + reorder_quantity > max_stock:
            reorder_quantity = max_stock - current_stock

        # Round up to nearest 5 or 10 for easier ordering
        if reorder_quantity > 0:
            if reorder_quantity <= 20:
                reorder_quantity = ((reorder_quantity + 4) // 5) * 5  # Round to 5
            else:
                reorder_quantity = ((reorder_quantity + 9) // 10) * 10  # Round to 10

        return max(0, int(reorder_quantity))

    def detect_velocity_anomalies(
        self, product_id: str, sales_history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect unusual changes in sales velocity

        Args:
            product_id: Product catalog ID
            sales_history: List of sales orders

        Returns:
            Anomaly details if detected, None otherwise
        """
        try:
            # Calculate velocity for recent period (7 days) vs baseline (30 days)
            recent_velocity = self.calculate_velocity(product_id, sales_history, days=7)
            baseline_velocity = self.calculate_velocity(
                product_id, sales_history, days=30
            )

            if baseline_velocity == 0:
                return None

            # Calculate percentage change
            change_percentage = (
                (recent_velocity - baseline_velocity) / baseline_velocity
            ) * 100

            # Flag significant changes (>50% increase or decrease)
            if abs(change_percentage) > 50:
                return {
                    "product_id": product_id,
                    "recent_velocity": recent_velocity,
                    "baseline_velocity": baseline_velocity,
                    "change_percentage": round(change_percentage, 1),
                    "direction": "increase" if change_percentage > 0 else "decrease",
                }

            return None

        except Exception as e:
            logger.error(
                f"Failed to detect anomalies for {product_id}: {str(e)}"
            )
            return None

    def calculate_optimal_stock_levels(
        self, velocity: float, lead_time_days: int = 7, service_level: float = 0.95
    ) -> Dict[str, int]:
        """
        Calculate optimal min/max stock levels

        Args:
            velocity: Units sold per day
            lead_time_days: Supplier lead time in days
            service_level: Desired service level (0-1)

        Returns:
            Dictionary with min_stock, max_stock, reorder_point
        """
        if velocity <= 0:
            return {"min_stock": 0, "max_stock": 0, "reorder_point": 0}

        # Safety stock calculation (simplified)
        # In production, would use standard deviation of demand
        safety_stock = velocity * lead_time_days * (1 - service_level)

        # Reorder point = lead time demand + safety stock
        reorder_point = (velocity * lead_time_days) + safety_stock

        # Min stock = safety stock
        min_stock = safety_stock

        # Max stock = 30 days of inventory (configurable)
        max_stock = velocity * 30

        return {
            "min_stock": int(min_stock),
            "max_stock": int(max_stock),
            "reorder_point": int(reorder_point),
        }
