"""
Widget CRUD API endpoints.
Phase 3: Added embed snippet and public config endpoint.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.widget import Widget
from app.schemas.widget import (
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetListResponse,
    WidgetConfig,
)

router = APIRouter()


def generate_embed_snippet(widget_id: str) -> str:
    """Generate HTML embed snippet for a widget."""
    base_url = settings.API_BASE_URL if hasattr(settings, 'API_BASE_URL') else "http://localhost:8000"
    return f'<script src="{base_url}/widget.v1.js?id={widget_id}"></script>'


@router.post("/", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    widget_data: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new widget for the authenticated user."""
    new_widget = Widget(
        owner_id=current_user.id,
        **widget_data.model_dump(),
    )
    db.add(new_widget)
    await db.flush()
    await db.refresh(new_widget)

    response = WidgetResponse.model_validate(new_widget)
    response.embed_snippet = generate_embed_snippet(new_widget.id)
    return response


@router.get("/", response_model=WidgetListResponse)
async def list_widgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all widgets owned by the authenticated user."""
    result = await db.execute(
        select(Widget).where(Widget.owner_id == current_user.id)
    )
    widgets = result.scalars().all()

    widget_responses = []
    for widget in widgets:
        response = WidgetResponse.model_validate(widget)
        response.embed_snippet = generate_embed_snippet(widget.id)
        widget_responses.append(response)

    return WidgetListResponse(widgets=widget_responses, total=len(widget_responses))


@router.get("/{widget_id}", response_model=WidgetResponse)
async def get_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific widget by ID (with tenant isolation)."""
    result = await db.execute(
        select(Widget).where(
            Widget.id == widget_id,
            Widget.owner_id == current_user.id,
        )
    )
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found",
        )

    response = WidgetResponse.model_validate(widget)
    response.embed_snippet = generate_embed_snippet(widget.id)
    return response


@router.patch("/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: str,
    widget_data: WidgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a specific widget (with tenant isolation)."""
    result = await db.execute(
        select(Widget).where(
            Widget.id == widget_id,
            Widget.owner_id == current_user.id,
        )
    )
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found",
        )

    update_data = widget_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(widget, field, value)

    await db.flush()
    await db.refresh(widget)

    response = WidgetResponse.model_validate(widget)
    response.embed_snippet = generate_embed_snippet(widget.id)
    return response


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific widget (with tenant isolation)."""
    result = await db.execute(
        select(Widget).where(
            Widget.id == widget_id,
            Widget.owner_id == current_user.id,
        )
    )
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found",
        )

    await db.delete(widget)


@router.get("/{widget_id}/config", response_model=WidgetConfig)
async def get_widget_config(
    widget_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint to get widget configuration for rendering.
    No authentication required.
    """
    result = await db.execute(
        select(Widget).where(Widget.id == widget_id)
    )
    widget = result.scalar_one_or_none()

    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found",
        )

    response.headers["Cache-Control"] = "public, max-age=300"

    return WidgetConfig(
        id=widget.id,
        title=widget.title,
        type=widget.type,
        button_text=widget.button_text,
        form_config=widget.form_config,
        display_options=widget.display_options,
    )
