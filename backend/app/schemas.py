"""
Pydantic schemas for the eigen knot Big Five Personality Assessment API.

Request / response models for:
  - Assessment submission (50 Likert-scale answers)
  - Assessment retrieval  (payment-gated Big Five results)
  - Payment webhook       (PortOne / Toss placeholder)
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────
# Assessment — Submit
# ──────────────────────────────────────────────

class AssessmentSubmitRequest(BaseModel):
    """Payload sent by the frontend widget after all 50 Big Five questions."""

    answers: list[int] = Field(
        ...,
        min_length=50,
        max_length=50,
        description="Exactly 50 Likert-scale responses (integers 1–5).",
    )

    @field_validator("answers", mode="before")
    @classmethod
    def validate_answer_values(cls, v: list[int]) -> list[int]:
        for i, val in enumerate(v):
            if not isinstance(val, int) or val < 1 or val > 5:
                raise ValueError(
                    f"Answer at index {i} must be an integer between 1 and 5, got {val!r}."
                )
        return v


class AssessmentSubmitResponse(BaseModel):
    status: str = "success"
    assessment_id: str


# ──────────────────────────────────────────────
# Assessment — Score structures
# ──────────────────────────────────────────────

class ScoreEntry(BaseModel):
    """A single score with both raw (1–5) and normalised (0–100) values."""
    raw: float
    score100: float


class ComparisonEntry(BaseModel):
    """Cross-domain comparison between two score dimensions."""
    left: str
    right: str
    diff: float
    higher: str


class BigFiveFullScores(BaseModel):
    """Complete scoring output — factors, sub-factors, and comparisons."""

    factors: dict[str, ScoreEntry] = Field(
        description="5 Big Five factor scores (agreeableness, openness_intellect, neuroticism, extraversion, conscientiousness)"
    )
    subfactors: dict[str, ScoreEntry] = Field(
        description="10 sub-factor scores"
    )
    comparisons: dict[str, ComparisonEntry] = Field(
        description="5 cross-domain comparison pairs"
    )


# ──────────────────────────────────────────────
# Assessment — Retrieve
# ──────────────────────────────────────────────

class AssessmentSummaryResponse(BaseModel):
    """Returned when is_paid is False — no detailed scores disclosed."""
    assessment_id: str
    status: str
    is_paid: bool
    created_at: datetime
    message: str = "결과를 확인하려면 결제가 필요합니다."


class AssessmentFullResponse(BaseModel):
    """Returned when is_paid is True — includes full Big Five personality profile."""
    assessment_id: str
    status: str
    is_paid: bool
    created_at: datetime
    scores: BigFiveFullScores


# ──────────────────────────────────────────────
# Payment Webhook
# ──────────────────────────────────────────────

class PaymentWebhookRequest(BaseModel):
    """Placeholder payload for PortOne / Toss payment webhook."""
    assessment_id: str
    payment_id: str | None = None
    status: str = "paid"


class PaymentWebhookResponse(BaseModel):
    status: str = "success"
    message: str = "Payment status updated."
