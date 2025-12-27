"""Tests for monitoring service"""

import pytest
from datetime import datetime
from src.services.monitor import MonitorService
from src.services.forecaster import ForecasterService
from src.models import AlertType, AlertSeverity


class TestMonitorService:
    """Test cases for MonitorService"""

    @pytest.fixture
    def monitor_service(self):
        """Create monitor service instance"""
        return MonitorService()

    @pytest.fixture
    def forecaster_service(self):
        """Create forecaster service instance"""
        return ForecasterService()

    def test_check_stock_levels(self, monitor_service):
        """Test stock level checking"""
        stock_levels = monitor_service.check_stock_levels("demo_location")

        assert len(stock_levels) > 0
        assert all("product_id" in s for s in stock_levels)
        assert all("current_stock" in s for s in stock_levels)
        assert all("status" in s for s in stock_levels)

    def test_generate_alerts_out_of_stock(self, monitor_service):
        """Test alert generation for out of stock items"""
        stock_levels = [
            {
                "product_id": "test_001",
                "product_name": "Test Product",
                "location_id": "loc_001",
                "current_stock": 0,
                "max_stock": 100,
                "stock_percentage": 0,
                "status": "out_of_stock",
            }
        ]

        alerts = monitor_service.generate_alerts(stock_levels)

        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.OUT_OF_STOCK
        assert alerts[0].severity == AlertSeverity.CRITICAL

    def test_generate_alerts_critical(self, monitor_service):
        """Test alert generation for critical stock levels"""
        stock_levels = [
            {
                "product_id": "test_002",
                "product_name": "Test Product 2",
                "location_id": "loc_001",
                "current_stock": 3,
                "max_stock": 100,
                "stock_percentage": 3,
                "status": "critical",
            }
        ]

        alerts = monitor_service.generate_alerts(stock_levels)

        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.CRITICAL_STOCK
        assert alerts[0].severity == AlertSeverity.CRITICAL

    def test_generate_alerts_low_stock(self, monitor_service):
        """Test alert generation for low stock levels"""
        stock_levels = [
            {
                "product_id": "test_003",
                "product_name": "Test Product 3",
                "location_id": "loc_001",
                "current_stock": 15,
                "max_stock": 100,
                "stock_percentage": 15,
                "status": "low",
            }
        ]

        alerts = monitor_service.generate_alerts(stock_levels)

        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.LOW_STOCK
        assert alerts[0].severity == AlertSeverity.WARNING

    def test_generate_alerts_healthy(self, monitor_service):
        """Test no alerts for healthy stock levels"""
        stock_levels = [
            {
                "product_id": "test_004",
                "product_name": "Test Product 4",
                "location_id": "loc_001",
                "current_stock": 80,
                "max_stock": 100,
                "stock_percentage": 80,
                "status": "healthy",
            }
        ]

        alerts = monitor_service.generate_alerts(stock_levels)

        assert len(alerts) == 0

    def test_calculate_velocity(self, forecaster_service):
        """Test velocity calculation"""
        sales_history = [
            {
                "id": "order_1",
                "created_at": datetime.now().isoformat(),
                "line_items": [{"catalog_object_id": "item_001", "quantity": "5"}],
            },
            {
                "id": "order_2",
                "created_at": datetime.now().isoformat(),
                "line_items": [{"catalog_object_id": "item_001", "quantity": "3"}],
            },
        ]

        velocity = forecaster_service.calculate_velocity(
            "item_001", sales_history, days=2
        )

        assert velocity == 4.0  # (5 + 3) / 2 days

    def test_calculate_days_until_stockout(self, forecaster_service):
        """Test stockout prediction"""
        days = forecaster_service.calculate_days_until_stockout(
            current_stock=20, velocity=5.0
        )

        assert days == 4  # 20 units / 5 per day

    def test_calculate_reorder_quantity(self, forecaster_service):
        """Test reorder quantity calculation"""
        reorder_qty = forecaster_service.calculate_reorder_quantity(
            velocity=5.0,
            current_stock=10,
            max_stock=100,
            lead_time_days=7,
            safety_stock_days=7,
        )

        # Should suggest ordering to cover 14 days (lead time + safety)
        # 5 units/day * 14 days = 70 units needed
        # Currently have 10, so need 60
        # Rounded to 60
        assert reorder_qty == 60

    def test_status_determination(self, monitor_service):
        """Test stock status determination"""
        assert monitor_service._determine_status(0, 0) == "out_of_stock"
        assert monitor_service._determine_status(3, 3) == "critical"
        assert monitor_service._determine_status(15, 15) == "low"
        assert monitor_service._determine_status(80, 80) == "healthy"
