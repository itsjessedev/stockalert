"""Square POS API integration"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from square.client import Client

from ..config import settings

logger = logging.getLogger(__name__)


class SquareService:
    """Service for interacting with Square POS API"""

    def __init__(self):
        self.demo_mode = settings.demo_mode
        if not self.demo_mode:
            self.client = Client(
                access_token=settings.square_access_token,
                environment=settings.square_environment,
            )

    def get_inventory_counts(self, location_id: str) -> List[Dict[str, Any]]:
        """Get current inventory counts for a location"""
        if self.demo_mode:
            return self._get_mock_inventory(location_id)

        try:
            result = self.client.inventory.batch_retrieve_inventory_counts(
                body={"location_ids": [location_id]}
            )

            if result.is_success():
                counts = result.body.get("counts", [])
                return [self._parse_inventory_count(count) for count in counts]
            else:
                logger.error(f"Square API error: {result.errors}")
                return []

        except Exception as e:
            logger.error(f"Failed to retrieve inventory: {str(e)}")
            return []

    def get_catalog_items(self, location_id: str) -> List[Dict[str, Any]]:
        """Get catalog items for a location"""
        if self.demo_mode:
            return self._get_mock_catalog()

        try:
            result = self.client.catalog.list_catalog(types="ITEM")

            if result.is_success():
                items = result.body.get("objects", [])
                return [self._parse_catalog_item(item) for item in items]
            else:
                logger.error(f"Square API error: {result.errors}")
                return []

        except Exception as e:
            logger.error(f"Failed to retrieve catalog: {str(e)}")
            return []

    def get_sales_history(
        self, location_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get sales history for velocity calculations"""
        if self.demo_mode:
            return self._get_mock_sales_history(location_id, days)

        try:
            start_date = datetime.now() - timedelta(days=days)
            result = self.client.orders.search_orders(
                body={
                    "location_ids": [location_id],
                    "query": {
                        "filter": {
                            "date_time_filter": {
                                "created_at": {
                                    "start_at": start_date.isoformat(),
                                }
                            }
                        }
                    },
                }
            )

            if result.is_success():
                orders = result.body.get("orders", [])
                return [self._parse_order(order) for order in orders]
            else:
                logger.error(f"Square API error: {result.errors}")
                return []

        except Exception as e:
            logger.error(f"Failed to retrieve sales history: {str(e)}")
            return []

    def _parse_inventory_count(self, count: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Square inventory count response"""
        return {
            "catalog_object_id": count.get("catalog_object_id"),
            "location_id": count.get("location_id"),
            "quantity": float(count.get("quantity", 0)),
            "calculated_at": count.get("calculated_at"),
        }

    def _parse_catalog_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Square catalog item response"""
        item_data = item.get("item_data", {})
        return {
            "id": item.get("id"),
            "name": item_data.get("name"),
            "description": item_data.get("description"),
            "category_id": item_data.get("category_id"),
        }

    def _parse_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Square order response"""
        return {
            "id": order.get("id"),
            "created_at": order.get("created_at"),
            "line_items": order.get("line_items", []),
            "total_money": order.get("total_money", {}),
        }

    def _get_mock_inventory(self, location_id: str) -> List[Dict[str, Any]]:
        """Get mock inventory data for demo mode"""
        return [
            {
                "catalog_object_id": "item_001",
                "location_id": location_id,
                "quantity": 45.0,
                "calculated_at": datetime.now().isoformat(),
            },
            {
                "catalog_object_id": "item_002",
                "location_id": location_id,
                "quantity": 8.0,
                "calculated_at": datetime.now().isoformat(),
            },
            {
                "catalog_object_id": "item_003",
                "location_id": location_id,
                "quantity": 120.0,
                "calculated_at": datetime.now().isoformat(),
            },
            {
                "catalog_object_id": "item_004",
                "location_id": location_id,
                "quantity": 2.0,
                "calculated_at": datetime.now().isoformat(),
            },
            {
                "catalog_object_id": "item_005",
                "location_id": location_id,
                "quantity": 0.0,
                "calculated_at": datetime.now().isoformat(),
            },
        ]

    def _get_mock_catalog(self) -> List[Dict[str, Any]]:
        """Get mock catalog data for demo mode"""
        return [
            {
                "id": "item_001",
                "name": "Premium Coffee Beans",
                "description": "Organic whole bean coffee",
                "category_id": "cat_beverages",
            },
            {
                "id": "item_002",
                "name": "Espresso Machine Filters",
                "description": "Replacement filters for espresso machine",
                "category_id": "cat_supplies",
            },
            {
                "id": "item_003",
                "name": "Paper Cups (16oz)",
                "description": "Disposable paper cups",
                "category_id": "cat_supplies",
            },
            {
                "id": "item_004",
                "name": "Vanilla Syrup",
                "description": "Flavoring syrup for beverages",
                "category_id": "cat_ingredients",
            },
            {
                "id": "item_005",
                "name": "Oat Milk",
                "description": "Dairy-free milk alternative",
                "category_id": "cat_ingredients",
            },
        ]

    def _get_mock_sales_history(
        self, location_id: str, days: int
    ) -> List[Dict[str, Any]]:
        """Get mock sales history for demo mode"""
        sales = []
        base_date = datetime.now() - timedelta(days=days)

        # Simulate sales over the period
        for day in range(days):
            sale_date = base_date + timedelta(days=day)
            # Item 1: 2-4 units per day
            sales.append(
                {
                    "id": f"order_{day}_1",
                    "created_at": sale_date.isoformat(),
                    "line_items": [{"catalog_object_id": "item_001", "quantity": "3"}],
                    "total_money": {"amount": 2400, "currency": "USD"},
                }
            )
            # Item 2: 0-1 units per day
            if day % 3 == 0:
                sales.append(
                    {
                        "id": f"order_{day}_2",
                        "created_at": sale_date.isoformat(),
                        "line_items": [
                            {"catalog_object_id": "item_002", "quantity": "1"}
                        ],
                        "total_money": {"amount": 500, "currency": "USD"},
                    }
                )
            # Item 3: 5-8 units per day
            sales.append(
                {
                    "id": f"order_{day}_3",
                    "created_at": sale_date.isoformat(),
                    "line_items": [{"catalog_object_id": "item_003", "quantity": "6"}],
                    "total_money": {"amount": 300, "currency": "USD"},
                }
            )
            # Item 4: 1-2 units per day
            sales.append(
                {
                    "id": f"order_{day}_4",
                    "created_at": sale_date.isoformat(),
                    "line_items": [{"catalog_object_id": "item_004", "quantity": "2"}],
                    "total_money": {"amount": 800, "currency": "USD"},
                }
            )
            # Item 5: 3-4 units per day
            sales.append(
                {
                    "id": f"order_{day}_5",
                    "created_at": sale_date.isoformat(),
                    "line_items": [{"catalog_object_id": "item_005", "quantity": "3"}],
                    "total_money": {"amount": 1200, "currency": "USD"},
                }
            )

        return sales
