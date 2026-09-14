"""
FlyRank Widget Platform - Main Application
Phase 2: Hardened Submission Path
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1 import api_router
from app.services.rate_limit import RateLimitMiddleware, RateLimitConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Embeddable Widget & Lead-Capture Platform API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware - Explicit configuration for customer websites
# In production, replace "*" with specific allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Development frontend
    "http://localhost:5500",  # VS Code Live Server
    "http://localhost:8080",  # Alternative dev server
    "http://localhost:8000",  # API itself (for testing)
]

# For development, allow all origins (remove in production)
if settings.DEBUG:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Rate limiting middleware for submission endpoint
app.add_middleware(
    RateLimitMiddleware,
    config=RateLimitConfig(max_requests=10, window_seconds=60),
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent 500 errors from leaking details."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    return {
        "message": "FlyRank Widget Platform API",
        "docs": "/docs",
        "version": "2.0.0",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
