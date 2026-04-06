"""
API routes for Organizational Value Mismatch Dynamics (OVMD) assessment.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, conlist
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import OVMDAssessment

router = APIRouter(prefix="/api/v1/ovmd", tags=["ovmd"])


class OVMDSubmitRequest(BaseModel):
    answers: conlist(int, min_length=18, max_length=18)


@router.post("/submit")
async def submit_ovmd_assessment(req: OVMDSubmitRequest, db: AsyncSession = Depends(get_db)):
    """
    Submits 18 answers and calculates the OVMD type scores.
    """
    answers = req.answers
    
    # 1-indexed to keep formula clean (0 index is dummy)
    ans = [0] + answers

    # The mapping
    scores = {
        "A": ans[1] + ans[7] + ans[13],
        "B": ans[2] + ans[8] + ans[14],
        "C": ans[3] + ans[9] + ans[15],
        "D": ans[4] + ans[10] + ans[16],
        "E": ans[5] + ans[11] + ans[17],
        "F": ans[6] + ans[12] + ans[18],
    }

    # Find the type with the highest score
    primary_type = max(scores, key=scores.get)

    new_assessment = OVMDAssessment(
        raw_answers=json.dumps(answers),
        type_scores=json.dumps(scores),
        primary_type=primary_type,
    )

    db.add(new_assessment)
    # The transaction commits via dependency when the route finishes
    await db.flush()  # Generate the ID proactively before commit if needed
    
    return {
        "status": "success",
        "assessment_id": new_assessment.id,
        "primary_type": primary_type,
        "scores": scores
    }


@router.get("/{assessment_id}")
async def get_ovmd_assessment(assessment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve completed OVMD assessment scores.
    """
    result = await db.execute(select(OVMDAssessment).where(OVMDAssessment.id == assessment_id))
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="OVMD Assessment not found.")

    return {
        "assessment_id": assessment.id,
        "created_at": assessment.created_at,
        "primary_type": assessment.primary_type,
        "scores": json.loads(assessment.type_scores) if assessment.type_scores else {},
    }
