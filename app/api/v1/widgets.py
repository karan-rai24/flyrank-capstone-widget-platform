"""
Widget CRUD API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.widget import Widget
from app.schemas.widget import (
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetListResponse,
)

router = APIRouter()


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

    return new_widget


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

    return WidgetListResponse(widgets=widgets, total=len(widgets))


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

    return widget


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

    # Update widget fields
    update_data = widget_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(widget, field, value)

    await db.flush()
    await db.refresh(widget)

    return widget


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
