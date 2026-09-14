"""
API v1 router.
Phase 3: Added dashboard endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import auth, widgets, submissions, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(widgets.router, prefix="/widgets", tags=["Widgets"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
