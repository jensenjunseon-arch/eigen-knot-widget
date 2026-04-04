"""
Assessment endpoints — Big Five Personality Assessment submission and retrieval.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Assessment
from app.schemas import (
    AssessmentFullResponse,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    AssessmentSummaryResponse,
    BigFiveFullScores,
)
from app.scoring import calculate_big_five_scores

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])


@router.post(
    "/submit",
    response_model=AssessmentSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Big Five personality assessment answers",
)
async def submit_assessment(
    payload: AssessmentSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> AssessmentSubmitResponse:
    """
    Receive 50 Likert-scale answers from the widget.

    1. Validate that exactly 50 integers (1–5) are received.
    2. Save raw answers to the database.
    3. Compute Big Five factor, sub-factor, and comparison scores **server-side**.
    4. Save all computed scores to the database.
    5. Return the generated assessment UUID.
    """
    answers = payload.answers

    # ── Server-side Big Five scoring ──
    scores = calculate_big_five_scores(answers)

    # ── Persist ──
    assessment = Assessment(
        raw_answers=json.dumps(answers, ensure_ascii=False),
        big_five_scores=json.dumps(scores["factors"], ensure_ascii=False),
        sub_factor_scores=json.dumps({
            "subfactors": scores["subfactors"],
            "comparisons": scores["comparisons"],
        }, ensure_ascii=False),
    )
    db.add(assessment)
    await db.flush()

    logger.info("Big Five assessment %s created", assessment.id)

    return AssessmentSubmitResponse(assessment_id=assessment.id)


@router.get(
    "/{assessment_id}",
    response_model=AssessmentSummaryResponse | AssessmentFullResponse,
    summary="Retrieve Big Five personality assessment results",
)
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
) -> AssessmentSummaryResponse | AssessmentFullResponse:
    """
    Retrieve an assessment by UUID.

    - If `is_paid` is **False** → returns a restricted summary (no scores).
    - If `is_paid` is **True**  → returns full Big Five personality profile.
    """
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    # TODO: Re-enable payment gating when payment integration is ready
    # if not assessment.is_paid:
    #     return AssessmentSummaryResponse(
    #         assessment_id=assessment.id,
    #         status="pending_payment",
    #         is_paid=False,
    #         created_at=assessment.created_at,
    #     )

    # Reconstruct the full scores object from stored JSON
    factors = json.loads(assessment.big_five_scores)
    extra = json.loads(assessment.sub_factor_scores)

    return AssessmentFullResponse(
        assessment_id=assessment.id,
        status="complete",
        is_paid=True,
        created_at=assessment.created_at,
        scores=BigFiveFullScores(
            factors=factors,
            subfactors=extra["subfactors"],
            comparisons=extra["comparisons"],
        ),
    )
