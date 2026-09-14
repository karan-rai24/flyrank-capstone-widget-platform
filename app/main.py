"""
FlyRank Widget Platform - Main Application
Phase 3: Delivery, Dashboard & Proof
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.api.v1 import api_router
from app.services.rate_limit import RateLimitMiddleware, RateLimitConfig

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    print(f"Starting {settings.APP_NAME}...")
    yield
    print(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Embeddable Widget & Lead-Capture Platform API",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8080",
    "http://localhost:8000",
]

if settings.DEBUG:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

app.add_middleware(
    RateLimitMiddleware,
    config=RateLimitConfig(max_requests=10, window_seconds=60),
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/widget.js")
@app.get("/widget.v1.js")
async def serve_widget():
    return FileResponse(
        STATIC_DIR / "widget.js",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@app.get("/")
async def root():
    return {
        "message": "FlyRank Widget Platform API",
        "docs": "/docs",
        "version": "3.0.0",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
