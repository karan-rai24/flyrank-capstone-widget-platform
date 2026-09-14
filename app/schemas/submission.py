"""
Submission schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class SubmissionBase(BaseModel):
    """Base submission schema."""
    submission_data: Dict[str, Any] = Field(..., description="Form submission data")


class SubmissionCreate(SubmissionBase):
    """Schema for creating a submission."""
    pass


class SubmissionResponse(SubmissionBase):
    """Schema for submission response."""
    id: str
    widget_id: str
    visitor_ip: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    """Schema for submission list response."""
    submissions: list[SubmissionResponse]
    total: int
