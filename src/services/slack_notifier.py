"""Slack notification service"""

import logging
from typing import List, Dict, Any
import requests

from ..models import Alert
from ..config import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Service for sending alerts to Slack"""

    def __init__(self):
        self.demo_mode = settings.demo_mode
        self.webhook_url = settings.slack_webhook_url

    def send_alert(self, alert: Alert) -> bool:
        """
        Send single alert to Slack

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully, False otherwise
        """
        if self.demo_mode:
            logger.info(f"[DEMO MODE] Would send Slack alert: {alert.message}")
            return True

        if not self.webhook_url:
            logger.warning("No Slack webhook URL configured")
            return False

        payload = self._format_alert_payload(alert)

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Slack alert sent successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack alert: {str(e)}")
            return False

    def send_batch_alerts(self, alerts: List[Alert]) -> Dict[str, int]:
        """
        Send multiple alerts to Slack as summary

        Args:
            alerts: List of alerts to send

        Returns:
            Dictionary with success/failure counts
        """
        if not alerts:
            return {"success": 0, "failed": 0}

        if self.demo_mode:
            logger.info(f"[DEMO MODE] Would send {len(alerts)} Slack alerts")
            return {"success": len(alerts), "failed": 0}

        # Send as summary with grouped alerts
        payload = self._format_batch_payload(alerts)

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Slack batch alert sent successfully")
            return {"success": len(alerts), "failed": 0}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack batch alert: {str(e)}")
            return {"success": 0, "failed": len(alerts)}

    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """
        Send daily inventory summary to Slack

        Args:
            summary_data: Summary statistics

        Returns:
            True if sent successfully
        """
        if self.demo_mode:
            logger.info("[DEMO MODE] Would send daily Slack summary")
            return True

        payload = self._format_summary_payload(summary_data)

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Slack daily summary sent successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack summary: {str(e)}")
            return False

    def _format_alert_payload(self, alert: Alert) -> Dict[str, Any]:
        """Format single alert for Slack"""
        color = {
            "critical": "#DC143C",  # Crimson
            "warning": "#FFA500",  # Orange
            "info": "#1E90FF",  # Dodger Blue
        }

        return {
            "attachments": [
                {
                    "color": color.get(alert.severity, "#808080"),
                    "title": f"StockAlert - {alert.alert_type.value.replace('_', ' ').title()}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Current Stock",
                            "value": str(alert.current_stock),
                            "short": True,
                        },
                        {
                            "title": "Severity",
                            "value": alert.severity.upper(),
                            "short": True,
                        },
                        {
                            "title": "Suggested Action",
                            "value": alert.suggested_action or "No action suggested",
                            "short": False,
                        },
                    ],
                    "footer": "StockAlert Monitoring System",
                    "ts": int(alert.created_at.timestamp()),
                }
            ]
        }

    def _format_batch_payload(self, alerts: List[Alert]) -> Dict[str, Any]:
        """Format multiple alerts for Slack"""
        # Group by severity
        critical = [a for a in alerts if a.severity == "critical"]
        warnings = [a for a in alerts if a.severity == "warning"]
        info = [a for a in alerts if a.severity == "info"]

        text = f"*Stock Alert Summary* - {len(alerts)} items need attention\n\n"

        if critical:
            text += f"🔴 *Critical ({len(critical)})*\n"
            for alert in critical[:3]:
                text += f"• {alert.message}\n"
            if len(critical) > 3:
                text += f"• ...and {len(critical) - 3} more critical items\n"
            text += "\n"

        if warnings:
            text += f"⚠️ *Warnings ({len(warnings)})*\n"
            for alert in warnings[:3]:
                text += f"• {alert.message}\n"
            if len(warnings) > 3:
                text += f"• ...and {len(warnings) - 3} more warnings\n"
            text += "\n"

        if info:
            text += f"ℹ️ *Info ({len(info)})*\n"
            for alert in info[:2]:
                text += f"• {alert.message}\n"
            if len(info) > 2:
                text += f"• ...and {len(info) - 2} more items\n"

        return {"text": text}

    def _format_summary_payload(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format daily summary for Slack"""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Daily Inventory Summary",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Products:*\n{summary_data.get('total_products', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Healthy Stock:*\n{summary_data.get('healthy', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Low Stock:*\n{summary_data.get('low_stock', 0)}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Critical/Out:*\n{summary_data.get('critical', 0)}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Alerts Generated:* {summary_data.get('alerts_generated', 0)}\n*Reorders Suggested:* {summary_data.get('reorders_suggested', 0)}",
                    },
                },
            ]
        }
