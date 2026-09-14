"""
Submission service for handling widget submissions.

This service orchestrates:
1. Widget validation
2. Submission validation
3. Rate limiting
4. Spam protection
5. Geo enrichment
6. Database storage
7. Notification
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.widget import Widget
from app.models.submission import Submission
from app.schemas.submission import PublicSubmissionCreate
from app.services.geo import GeoEnrichmentService, geo_service
from app.services.notification import (
    NotificationService,
    NotificationPayload,
    notification_service,
)
from app.services.rate_limit import RateLimitService, submission_rate_limiter

logger = logging.getLogger(__name__)


class SubmissionService:
    """
    Service for processing widget submissions.
    """

    def __init__(
        self,
        geo_service_instance: Optional[GeoEnrichmentService] = None,
        notification_service_instance: Optional[NotificationService] = None,
        rate_limiter: Optional[RateLimitService] = None,
    ):
        self.geo_service = geo_service_instance or geo_service
        self.notification_service = notification_service_instance or notification_service
        self.rate_limiter = rate_limiter or submission_rate_limiter

    async def validate_widget(
        self, db: AsyncSession, widget_id: str
    ) -> Optional[Widget]:
        """Validate that widget exists and is active."""
        result = await db.execute(
            select(Widget).where(Widget.id == widget_id)
        )
        return result.scalar_one_or_none()

    def check_rate_limit(self, visitor_ip: str) -> bool:
        """Check rate limit for visitor IP."""
        key = f"submission:{visitor_ip}"
        if not self.rate_limiter.check_rate_limit(key):
            return False
        self.rate_limiter.record_request(key)
        return True

    def check_honeypot(self, honeypot: Optional[str]) -> bool:
        """
        Check honeypot field.
        Returns True if legitimate, False if spam.
        """
        if honeypot and honeypot.strip():
            logger.info(f"Honeypot triggered: {honeypot[:20]}...")
            return False
        return True

    async def enrich_geo(self, visitor_ip: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempt geo enrichment.
        Returns (country, city) or (None, None) if both providers fail.
        """
        if not visitor_ip:
            return None, None

        geo_data = await self.geo_service.enrich(visitor_ip)
        if geo_data:
            return geo_data.country, geo_data.city
        return None, None

    async def store_submission(
        self,
        db: AsyncSession,
        widget_id: str,
        submission_data: dict,
        visitor_ip: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Submission:
        """Store submission in database."""
        submission = Submission(
            id=str(uuid.uuid4()),
            widget_id=widget_id,
            submission_data=submission_data,
            visitor_ip=visitor_ip,
            country=country,
            city=city,
            created_at=datetime.now(timezone.utc),
        )
        db.add(submission)
        await db.flush()
        await db.refresh(submission)
        return submission

    async def send_notification(
        self,
        submission: Submission,
        widget: Widget,
    ) -> bool:
        """Send notification for new submission (safe side effect)."""
        try:
            payload = NotificationPayload(
                submission_id=submission.id,
                widget_id=widget.id,
                widget_title=widget.title,
                submission_data=submission.submission_data,
                visitor_ip=submission.visitor_ip,
                country=submission.country,
                city=submission.city,
                created_at=submission.created_at,
            )
            return await self.notification_service.notify_submission(payload)
        except Exception as e:
            # Never let notification failure affect submission
            logger.error(f"Notification failed for submission {submission.id}: {e}")
            return False

    async def process_submission(
        self,
        db: AsyncSession,
        submission_data: PublicSubmissionCreate,
        visitor_ip: Optional[str] = None,
    ) -> Tuple[Optional[Submission], Optional[str]]:
        """
        Process a complete submission.

        Returns:
            (Submission, error_message) tuple
            - If successful: (Submission, None)
            - If failed: (None, error_message)
        """
        # 1. Check honeypot (spam protection)
        if not self.check_honeypot(submission_data.honeypot):
            logger.info(f"Spam submission blocked for widget {submission_data.widget_id}")
            return None, "Submission rejected"

        # 2. Check rate limit
        ip = visitor_ip or "unknown"
        if not self.check_rate_limit(ip):
            logger.warning(f"Rate limit exceeded for {ip}")
            return None, "Rate limit exceeded"

        # 3. Validate widget exists
        widget = await self.validate_widget(db, submission_data.widget_id)
        if not widget:
            return None, "Widget not found"

        # 4. Geo enrichment (with fallback)
        country, city = await self.enrich_geo(ip)

        # 5. Store submission
        submission = await self.store_submission(
            db=db,
            widget_id=submission_data.widget_id,
            submission_data=submission_data.submission_data,
            visitor_ip=ip,
            country=country,
            city=city,
        )

        # 6. Send notification (safe side effect - doesn't affect submission)
        await self.send_notification(submission, widget)

        return submission, None


# Singleton instance
submission_service = SubmissionService()
