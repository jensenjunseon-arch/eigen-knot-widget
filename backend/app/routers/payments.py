"""
Payment webhook endpoint — placeholder for PortOne / Toss integration.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Assessment
from app.schemas import PaymentWebhookRequest, PaymentWebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post(
    "/webhook",
    response_model=PaymentWebhookResponse,
    summary="Payment success webhook (placeholder)",
)
async def payment_webhook(
    payload: PaymentWebhookRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentWebhookResponse:
    """
    Receives a payment confirmation from the payment gateway.

    In production this endpoint should:
      1. Verify the webhook signature using PAYMENT_WEBHOOK_SECRET.
      2. Validate the payment amount and status with the gateway API.
      3. Only then mark `is_paid = True`.

    For now it is a simple placeholder that trusts the incoming payload.
    """
    result = await db.execute(
        select(Assessment).where(Assessment.id == payload.assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    assessment.is_paid = True
    db.add(assessment)

    logger.info(
        "Assessment %s marked as paid (payment_id=%s)",
        assessment.id,
        payload.payment_id,
    )

    return PaymentWebhookResponse()
