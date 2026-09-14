"""
Widget schemas for request/response validation.
Phase 3: Updated with embed snippet support.
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class WidgetBase(BaseModel):
    """Base widget schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Widget title")
    description: Optional[str] = Field(None, description="Widget description")
    type: str = Field(default="lead_capture", description="Widget type")
    button_text: str = Field(default="Submit", max_length=100, description="Button text")
    form_config: Optional[Dict[str, Any]] = Field(None, description="Form configuration")
    display_options: Optional[Dict[str, Any]] = Field(None, description="Display options")


class WidgetCreate(WidgetBase):
    """Schema for creating a widget."""
    pass


class WidgetUpdate(BaseModel):
    """Schema for updating a widget."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    type: Optional[str] = None
    button_text: Optional[str] = Field(None, max_length=100)
    form_config: Optional[Dict[str, Any]] = None
    display_options: Optional[Dict[str, Any]] = None


class WidgetResponse(WidgetBase):
    """Schema for widget response with embed snippet."""
    id: str
    owner_id: str
    embed_snippet: str = Field(description="HTML embed snippet for this widget")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WidgetListResponse(BaseModel):
    """Schema for widget list response."""
    widgets: list[WidgetResponse]
    total: int


class WidgetConfig(BaseModel):
    """Public widget configuration for rendering."""
    id: str
    title: str
    type: str
    button_text: str
    form_config: Optional[Dict[str, Any]] = None
    display_options: Optional[Dict[str, Any]] = None
