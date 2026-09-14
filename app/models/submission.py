"""
Submission model.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Submission(Base):
    """Submission model for visitor form submissions."""

    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    widget_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("widgets.id"), nullable=False, index=True
    )
    submission_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    visitor_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    widget = relationship("Widget", back_populates="submissions")

    def __repr__(self) -> str:
        return f"<Submission {self.id} for Widget {self.widget_id}>"
