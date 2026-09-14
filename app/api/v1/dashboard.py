"""
Dashboard API endpoints for widget owners.
Phase 3: Submission list and analytics.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.widget import Widget
from app.models.submission import Submission
from app.schemas.submission import SubmissionResponse, SubmissionListResponse

router = APIRouter()


@router.get("/submissions", response_model=SubmissionListResponse)
async def get_submissions(
    widget_id: Optional[str] = Query(None, description="Filter by widget ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get submissions for the authenticated user's widgets.
    Tenant isolation: Only returns submissions from widgets owned by the user.
    """
    user_widget_ids = await get_user_widget_ids(db, current_user.id)

    if not user_widget_ids:
        return SubmissionListResponse(submissions=[], total=0)

    query = select(Submission).where(Submission.widget_id.in_(user_widget_ids))

    if widget_id:
        if widget_id not in user_widget_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this widget",
            )
        query = query.where(Submission.widget_id == widget_id)

    if start_date:
        query = query.where(Submission.created_at >= start_date)
    if end_date:
        query = query.where(Submission.created_at <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Submission.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    submissions = result.scalars().all()

    return SubmissionListResponse(submissions=submissions, total=total)


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for the authenticated user's widgets.
    Tenant isolation: Only returns stats from widgets owned by the user.
    """
    user_widget_ids = await get_user_widget_ids(db, current_user.id)

    if not user_widget_ids:
        return {
            "total_submissions": 0,
            "widgets": {},
            "recent_submissions": 0,
            "geo_breakdown": {"countries": {}, "cities": {}},
        }

    total_result = await db.execute(
        select(func.count()).where(Submission.widget_id.in_(user_widget_ids))
    )
    total_submissions = total_result.scalar()

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_result = await db.execute(
        select(func.count()).where(
            and_(
                Submission.widget_id.in_(user_widget_ids),
                Submission.created_at >= week_ago,
            )
        )
    )
    recent_submissions = recent_result.scalar()

    widgets_stats = {}
    for widget_id in user_widget_ids:
        widget_result = await db.execute(
            select(func.count()).where(Submission.widget_id == widget_id)
        )
        widgets_stats[widget_id] = widget_result.scalar()

    country_result = await db.execute(
        select(Submission.country, func.count())
        .where(
            and_(
                Submission.widget_id.in_(user_widget_ids),
                Submission.country.isnot(None),
            )
        )
        .group_by(Submission.country)
    )
    countries = {row[0]: row[1] for row in country_result.all()}

    city_result = await db.execute(
        select(Submission.city, func.count())
        .where(
            and_(
                Submission.widget_id.in_(user_widget_ids),
                Submission.city.isnot(None),
            )
        )
        .group_by(Submission.city)
    )
    cities = {row[0]: row[1] for row in city_result.all()}

    return {
        "total_submissions": total_submissions,
        "widgets": widgets_stats,
        "recent_submissions": recent_submissions,
        "geo_breakdown": {
            "countries": countries,
            "cities": cities,
        },
    }


async def get_user_widget_ids(db: AsyncSession, user_id: str) -> list[str]:
    """Get all widget IDs owned by a user."""
    result = await db.execute(
        select(Widget.id).where(Widget.owner_id == user_id)
    )
    return [row[0] for row in result.all()]
