"""
API v1 router.
"""
from fastapi import APIRouter

from app.api.v1 import auth, widgets

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(widgets.router, prefix="/widgets", tags=["Widgets"])
