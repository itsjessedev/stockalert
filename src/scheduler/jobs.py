"""Background monitoring jobs"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from ..config import settings
from ..services import MonitorService, TwilioNotifier, SlackNotifier

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
monitor_service = MonitorService()
twilio_notifier = TwilioNotifier()
slack_notifier = SlackNotifier()


def check_inventory_job():
    """Background job to check inventory and send alerts"""
    logger.info("Running scheduled inventory check")

    try:
        # Get all locations (in production, query from database)
        location_ids = ["loc_001", "loc_002", "loc_003"]

        all_alerts = []
        for location_id in location_ids:
            # Check stock levels
            stock_levels = monitor_service.check_stock_levels(location_id)

            # Generate alerts
            alert_creates = monitor_service.generate_alerts(stock_levels)

            if alert_creates:
                # Convert to Alert objects
                from datetime import datetime
                import uuid
                from ..models import Alert

                for ac in alert_creates:
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        product_id=ac.product_id,
                        location_id=ac.location_id,
                        alert_type=ac.alert_type,
                        severity=ac.severity,
                        message=ac.message,
                        current_stock=ac.current_stock,
                        suggested_action=ac.suggested_action,
                        acknowledged=False,
                        created_at=datetime.now(),
                    )
                    all_alerts.append(alert)

        if all_alerts:
            logger.info(f"Generated {len(all_alerts)} alerts")

            # Send notifications
            # SMS for critical alerts only
            critical_alerts = [a for a in all_alerts if a.severity == "critical"]
            if critical_alerts:
                twilio_notifier.send_batch_alerts(critical_alerts)

            # Slack for all alerts
            slack_notifier.send_batch_alerts(all_alerts)

        else:
            logger.info("No alerts generated - all stock levels healthy")

    except Exception as e:
        logger.error(f"Error in scheduled inventory check: {str(e)}")


def daily_summary_job():
    """Send daily inventory summary"""
    logger.info("Generating daily summary")

    try:
        location_ids = ["loc_001", "loc_002", "loc_003"]

        total_products = 0
        healthy = 0
        low_stock = 0
        critical = 0
        alerts_generated = 0
        reorders_suggested = 0

        for location_id in location_ids:
            stock_levels = monitor_service.check_stock_levels(location_id)
            alert_creates = monitor_service.generate_alerts(stock_levels)

            total_products += len(stock_levels)
            healthy += sum(1 for s in stock_levels if s["status"] == "healthy")
            low_stock += sum(1 for s in stock_levels if s["status"] == "low")
            critical += sum(
                1
                for s in stock_levels
                if s["status"] in ["critical", "out_of_stock"]
            )
            alerts_generated += len(alert_creates)
            reorders_suggested += sum(
                1 for s in stock_levels if s.get("suggested_reorder_quantity", 0) > 0
            )

        summary_data = {
            "total_products": total_products,
            "healthy": healthy,
            "low_stock": low_stock,
            "critical": critical,
            "alerts_generated": alerts_generated,
            "reorders_suggested": reorders_suggested,
        }

        slack_notifier.send_daily_summary(summary_data)

    except Exception as e:
        logger.error(f"Error generating daily summary: {str(e)}")


def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        # Check inventory at configured interval
        scheduler.add_job(
            check_inventory_job,
            trigger=IntervalTrigger(minutes=settings.check_interval_minutes),
            id="inventory_check",
            name="Check inventory levels",
            replace_existing=True,
        )

        # Daily summary at 8 AM
        scheduler.add_job(
            daily_summary_job,
            trigger="cron",
            hour=8,
            minute=0,
            id="daily_summary",
            name="Send daily summary",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
