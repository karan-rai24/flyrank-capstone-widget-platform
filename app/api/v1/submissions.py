"""
Public submission API endpoint.

Phase 2: Hardened Submission Path with Idempotency Support.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.submission import (
    PublicSubmissionCreate,
    SubmissionAccepted,
    SubmissionError,
)
from app.services.submission import submission_service
from app.services.idempotency import (
    idempotency_service,
    get_idempotency_key,
)

router = APIRouter()


@router.post(
    "/",
    response_model=SubmissionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": SubmissionError, "description": "Invalid request"},
        404: {"model": SubmissionError, "description": "Widget not found"},
        413: {"model": SubmissionError, "description": "Payload too large"},
        422: {"model": SubmissionError, "description": "Validation error"},
        429: {"model": SubmissionError, "description": "Rate limit exceeded"},
    },
)
async def submit_to_widget(
    request: Request,
    submission: PublicSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Depends(get_idempotency_key),
):
    """
    Public endpoint for submitting data to a widget.

    This endpoint:
    1. Validates the submission
    2. Checks idempotency (if key provided)
    3. Checks rate limits
    4. Checks honeypot (spam protection)
    5. Enriches with geo data
    6. Stores submission
    7. Sends notification (safe side effect)

    Does NOT require authentication - this is a public endpoint.
    """
    if idempotency_key:
        existing = idempotency_service.get(idempotency_key)
        if existing:
            return SubmissionAccepted(**existing.response_data)

    visitor_ip = request.client.host if request.client else None

    if not visitor_ip or visitor_ip == "unknown":
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            visitor_ip = forwarded_for.split(",")[0].strip()

    result, error = await submission_service.process_submission(
        db=db,
        submission_data=submission,
        visitor_ip=visitor_ip,
    )

    if error:
        if error == "Widget not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error,
            )
        elif error == "Rate limit exceeded":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error,
                headers={"Retry-After": "60"},
            )
        elif error == "Submission rejected":
            response_data = {
                "id": "placeholder",
                "message": "Submission received successfully",
            }
            if idempotency_key:
                idempotency_service.set(idempotency_key, response_data, 202)
            return SubmissionAccepted(**response_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )

    response_data = {
        "id": result.id,
        "message": "Submission received successfully",
    }

    if idempotency_key:
        idempotency_service.set(idempotency_key, response_data, 202)

    return SubmissionAccepted(**response_data)
