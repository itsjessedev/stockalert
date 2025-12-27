"""Alerts API endpoints"""

from typing import List
from fastapi import APIRouter, HTTPException, Query
from ..models import Alert, AlertCreate
from ..services import MonitorService, TwilioNotifier, SlackNotifier

router = APIRouter(prefix="/alerts", tags=["alerts"])
monitor_service = MonitorService()
twilio_notifier = TwilioNotifier()
slack_notifier = SlackNotifier()


@router.get("/", response_model=List[Alert])
async def get_alerts(
    location_id: str = Query(None, description="Filter by location ID"),
    severity: str = Query(None, description="Filter by severity (info/warning/critical)"),
    acknowledged: bool = Query(None, description="Filter by acknowledgment status"),
):
    """
    Get all alerts with optional filtering

    Returns list of alerts matching the specified filters
    """
    # In production, this would query a database
    # For demo, we'll generate current alerts
    try:
        stock_levels = monitor_service.check_stock_levels(
            location_id or "demo_location"
        )
        alert_creates = monitor_service.generate_alerts(stock_levels)

        # Convert AlertCreate to Alert (with mock IDs and timestamps)
        from datetime import datetime
        import uuid

        alerts = []
        for i, ac in enumerate(alert_creates):
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
            alerts.append(alert)

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check")
async def check_and_alert(
    location_id: str = Query(..., description="Location ID to check"),
    send_sms: bool = Query(False, description="Send SMS notifications"),
    send_slack: bool = Query(True, description="Send Slack notifications"),
):
    """
    Check inventory and send alerts if needed

    Checks stock levels, generates alerts, and sends notifications via configured channels
    """
    try:
        # Check stock levels
        stock_levels = monitor_service.check_stock_levels(location_id)

        # Generate alerts
        alert_creates = monitor_service.generate_alerts(stock_levels)

        if not alert_creates:
            return {
                "status": "success",
                "message": "No alerts generated - all stock levels healthy",
                "alerts_count": 0,
            }

        # Convert to Alert objects for notification services
        from datetime import datetime
        import uuid

        alerts = []
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
            alerts.append(alert)

        # Send notifications
        notifications_sent = []

        if send_sms:
            sms_result = twilio_notifier.send_batch_alerts(alerts)
            notifications_sent.append(f"SMS: {sms_result['success']} sent")

        if send_slack:
            slack_result = slack_notifier.send_batch_alerts(alerts)
            notifications_sent.append(f"Slack: {slack_result['success']} sent")

        return {
            "status": "success",
            "message": "Alerts generated and notifications sent",
            "alerts_count": len(alerts),
            "notifications": notifications_sent,
            "alerts": [
                {
                    "severity": a.severity,
                    "message": a.message,
                    "action": a.suggested_action,
                }
                for a in alerts
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Mark an alert as acknowledged

    Updates alert status to acknowledged and records who/when
    """
    # In production, this would update the database
    return {
        "status": "success",
        "message": f"Alert {alert_id} acknowledged",
        "alert_id": alert_id,
    }
