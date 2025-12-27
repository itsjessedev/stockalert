"""Twilio SMS notification service"""

import logging
from typing import List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from ..models import Alert
from ..config import settings

logger = logging.getLogger(__name__)


class TwilioNotifier:
    """Service for sending SMS alerts via Twilio"""

    def __init__(self):
        self.demo_mode = settings.demo_mode
        if not self.demo_mode:
            self.client = Client(
                settings.twilio_account_sid, settings.twilio_auth_token
            )
        self.from_number = settings.twilio_from_number
        self.to_numbers = settings.twilio_to_numbers_list

    def send_alert(self, alert: Alert) -> bool:
        """
        Send SMS alert for a single alert

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully, False otherwise
        """
        if self.demo_mode:
            logger.info(f"[DEMO MODE] Would send SMS alert: {alert.message}")
            return True

        if not self.to_numbers:
            logger.warning("No phone numbers configured for SMS alerts")
            return False

        message_body = self._format_alert_message(alert)

        success = True
        for to_number in self.to_numbers:
            try:
                message = self.client.messages.create(
                    body=message_body, from_=self.from_number, to=to_number
                )
                logger.info(f"SMS sent to {to_number}: {message.sid}")
            except TwilioRestException as e:
                logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
                success = False

        return success

    def send_batch_alerts(self, alerts: List[Alert]) -> Dict[str, int]:
        """
        Send multiple alerts via SMS

        Args:
            alerts: List of alerts to send

        Returns:
            Dictionary with success/failure counts
        """
        if not alerts:
            return {"success": 0, "failed": 0}

        if self.demo_mode:
            logger.info(f"[DEMO MODE] Would send {len(alerts)} SMS alerts")
            return {"success": len(alerts), "failed": 0}

        # Group alerts by severity for batching
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        other_alerts = [a for a in alerts if a.severity != "critical"]

        success_count = 0
        failed_count = 0

        # Send critical alerts individually
        for alert in critical_alerts:
            if self.send_alert(alert):
                success_count += 1
            else:
                failed_count += 1

        # Batch other alerts into summary message
        if other_alerts:
            summary = self._format_summary_message(other_alerts)
            if self._send_message(summary):
                success_count += len(other_alerts)
            else:
                failed_count += len(other_alerts)

        return {"success": success_count, "failed": failed_count}

    def _format_alert_message(self, alert: Alert) -> str:
        """Format a single alert for SMS"""
        severity_emoji = {
            "critical": "🔴",
            "warning": "⚠️",
            "info": "ℹ️",
        }

        emoji = severity_emoji.get(alert.severity, "")
        message = f"{emoji} StockAlert - {alert.alert_type.value.upper()}\n\n"
        message += f"{alert.message}\n"

        if alert.suggested_action:
            message += f"\nAction: {alert.suggested_action}"

        return message

    def _format_summary_message(self, alerts: List[Alert]) -> str:
        """Format multiple alerts into summary message"""
        message = f"📊 StockAlert Summary - {len(alerts)} items need attention:\n\n"

        for alert in alerts[:5]:  # Limit to 5 to keep SMS short
            message += f"• {alert.message}\n"

        if len(alerts) > 5:
            message += f"\n...and {len(alerts) - 5} more. Check dashboard for details."

        return message

    def _send_message(self, message_body: str) -> bool:
        """Send message to all configured numbers"""
        if not self.to_numbers:
            return False

        success = True
        for to_number in self.to_numbers:
            try:
                message = self.client.messages.create(
                    body=message_body, from_=self.from_number, to=to_number
                )
                logger.info(f"SMS sent to {to_number}: {message.sid}")
            except TwilioRestException as e:
                logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
                success = False

        return success
