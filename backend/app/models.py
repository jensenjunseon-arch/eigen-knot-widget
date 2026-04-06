"""
SQLAlchemy ORM model for the Big Five Personality Assessment.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


class Assessment(Base):
    """
    Stores one completed Big Five personality assessment session.

    Each row represents a single respondent's submission containing:
    - The 50 raw Likert-scale answers
    - Server-computed Big Five factor scores (5 factors, 0–100)
    - Server-computed sub-factor scores (10 sub-factors, 0–100)
    - Payment status that gates access to the full result report
    """

    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Raw Likert-scale responses as JSON list  [4, 2, 5, ...]
    raw_answers: Mapped[str] = mapped_column(Text, nullable=False)

    # Big Five factor scores (0–100) as JSON
    # e.g. {"agreeableness": 72.5, "openness_intellect": 65.0, ...}
    big_five_scores: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sub-factor scores (0–100) as JSON
    # e.g. {"compassion": 75.0, "politeness": 70.0, ...}
    sub_factor_scores: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Payment status — unlocks full personality report
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class OVMDAssessment(Base):
    """
    Stores one completed Organizational Value Mismatch Dynamics (OVMD) session.
    """

    __tablename__ = "ovmd_assessments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Raw 1-5 scale responses (18 items)
    raw_answers: Mapped[str] = mapped_column(Text, nullable=False)

    # Scores for A through F types
    # e.g. {"A": 10, "B": 15, "C": ...}
    type_scores: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Best-matching type
    primary_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
