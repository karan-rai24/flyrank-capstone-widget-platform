"""
Submission schemas for request/response validation.
Phase 2: Hardened Submission Path
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator


class PublicSubmissionCreate(BaseModel):
    """
    Schema for public widget submission.
    This is what a visitor submits through the embedded widget.
    """
    widget_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        description="Widget ID to submit to"
    )
    submission_data: Dict[str, Any] = Field(
        ...,
        description="Form field data (name, email, message, etc.)"
    )
    honeypot: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Hidden field for spam detection - must be empty"
    )

    @field_validator('widget_id')
    @classmethod
    def validate_widget_id(cls, v: str) -> str:
        """Validate widget ID format."""
        if not v.strip():
            raise ValueError('Widget ID cannot be empty or whitespace')
        return v.strip()

    @field_validator('submission_data')
    @classmethod
    def validate_submission_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate submission data constraints."""
        import json

        # Check payload size (max 64KB)
        payload_size = len(json.dumps(v).encode('utf-8'))
        if payload_size > 65536:  # 64KB
            raise ValueError('Submission data too large (max 64KB)')

        # Check number of fields
        if len(v) > 50:
            raise ValueError('Too many fields (max 50)')

        # Validate field names (no empty keys)
        for key in v.keys():
            if not key.strip():
                raise ValueError('Field names cannot be empty')

        return v

    @field_validator('honeypot')
    @classmethod
    def validate_honeypot(cls, v: Optional[str]) -> Optional[str]:
        """
        Honeypot should be empty for legitimate users.
        If filled, it's likely a bot.
        """
        if v and v.strip():
            # Return the value - will be checked in the endpoint
            return v
        return None


class SubmissionCreate(BaseModel):
    """Schema for internal submission creation (from authenticated endpoints)."""
    widget_id: str
    submission_data: Dict[str, Any]
    visitor_ip: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None


class SubmissionResponse(BaseModel):
    """Schema for submission response."""
    id: str
    widget_id: str
    submission_data: Dict[str, Any]
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


class SubmissionAccepted(BaseModel):
    """Schema for accepted submission response."""
    id: str
    message: str = "Submission received successfully"


class SubmissionError(BaseModel):
    """Schema for submission error response."""
    detail: str
    error_code: Optional[str] = None
