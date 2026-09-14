"""
Notification service for submission side effects.

This service handles secondary effects after a submission is stored.
If notification fails, the submission remains successful.
"""
import logging
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class NotificationPayload:
    """Payload for submission notification."""
    submission_id: str
    widget_id: str
    widget_title: str
    submission_data: dict
    visitor_ip: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    created_at: Optional[datetime] = None


class NotificationProvider:
    """Base class for notification providers."""

    async def send(self, payload: NotificationPayload) -> bool:
        """
        Send notification.
        Returns True if successful, False otherwise.
        """
        raise NotImplementedError


class ConsoleNotificationProvider(NotificationProvider):
    """
    Console notification provider for development.
    Prints submission details to stdout.
    """

    async def send(self, payload: NotificationPayload) -> bool:
        try:
            print("\n" + "=" * 60)
            print("📩 NEW SUBMISSION RECEIVED")
            print("=" * 60)
            print(f"  Submission ID: {payload.submission_id}")
            print(f"  Widget: {payload.widget_title} ({payload.widget_id})")
            print(f"  Data: {payload.submission_data}")
            if payload.visitor_ip:
                location = []
                if payload.city:
                    location.append(payload.city)
                if payload.country:
                    location.append(payload.country)
                location_str = ", ".join(location) if location else "Unknown"
                print(f"  Visitor: {payload.visitor_ip} ({location_str})")
            print(f"  Time: {payload.created_at or datetime.now(timezone.utc)}")
            print("=" * 60 + "\n")
            return True
        except Exception as e:
            logger.error(f"Console notification failed: {e}")
            return False


class WebhookNotificationProvider(NotificationProvider):
    """
    Webhook notification provider.
    Sends POST request to configured URL.
    """

    def __init__(self, webhook_url: str, timeout: float = 5.0):
        self.webhook_url = webhook_url
        self.timeout = timeout

    async def send(self, payload: NotificationPayload) -> bool:
        try:
            import httpx

            data = {
                "submission_id": payload.submission_id,
                "widget_id": payload.widget_id,
                "widget_title": payload.widget_title,
                "submission_data": payload.submission_data,
                "visitor_ip": payload.visitor_ip,
                "country": payload.country,
                "city": payload.city,
                "created_at": payload.created_at.isoformat() if payload.created_at else None,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.webhook_url, json=data)
                response.raise_for_status()
                logger.info(f"Webhook notification sent for submission {payload.submission_id}")
                return True
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False


class NotificationService:
    """
    Notification service with provider fallback.

    If notification fails, the submission remains successful.
    This is a safe side effect.
    """

    def __init__(self, provider: Optional[NotificationProvider] = None):
        self.provider = provider or ConsoleNotificationProvider()

    async def notify_submission(self, payload: NotificationPayload) -> bool:
        """
        Send notification for new submission.

        Returns True if successful, False otherwise.
        Failure does NOT affect the submission.
        """
        try:
            success = await self.provider.send(payload)
            if success:
                logger.info(f"Notification sent for submission {payload.submission_id}")
            else:
                logger.warning(f"Notification failed for submission {payload.submission_id}")
            return success
        except Exception as e:
            # Never let notification failure affect the submission
            logger.error(f"Notification error for submission {payload.submission_id}: {e}")
            return False


# Singleton instance for the application
notification_service = NotificationService()
