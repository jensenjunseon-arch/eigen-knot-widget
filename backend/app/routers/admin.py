"""
Admin routes for Eigen Knot assessment platform.
Provides secure data export capabilities.
"""

import csv
import json
from datetime import datetime
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Assessment

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

def verify_admin(admin_key: str = Query(..., description="Admin password to access data")):
    """Dependency to check admin password."""
    if admin_key != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")
    return True

@router.get("/assessments")
async def list_assessments(
    _authorized: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Return recent assessments as JSON for the admin dashboard UI.
    """
    result = await db.execute(select(Assessment).order_by(Assessment.created_at.desc()).limit(100))
    records = result.scalars().all()
    
    data = []
    for r in records:
        try:
            f_scores = json.loads(r.big_five_scores) if r.big_five_scores else {}
        except:
            f_scores = {}
        data.append({
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "is_paid": r.is_paid,
            "extraversion": f_scores.get("extraversion", {}).get("score100", 0),
            "agreeableness": f_scores.get("agreeableness", {}).get("score100", 0),
            "conscientiousness": f_scores.get("conscientiousness", {}).get("score100", 0),
            "neuroticism": f_scores.get("neuroticism", {}).get("score100", 0),
            "openness": f_scores.get("openness_intellect", {}).get("score100", 0),
        })
    return {"status": "success", "count": len(data), "data": data}

@router.get("/assessments/csv")
async def export_assessments_csv(
    _authorized: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Export all assessment results as a CSV file.
    """
    result = await db.execute(select(Assessment).order_by(Assessment.created_at.desc()))
    assessments = result.scalars().all()

    # Create CSV in memory
    stream = StringIO()
    writer = csv.writer(stream)

    # Make headers
    headers = [
        "Assessment ID", "Created At", "Is Paid",
        # 5 Factors
        "Factor_Ext", "Factor_Agr", "Factor_Con", "Factor_Neuro", "Factor_Open",
        # 10 Subfactors
        "Sub_Compassion", "Sub_Politeness", "Sub_Industriousness", "Sub_Orderliness",
        "Sub_Enthusiasm", "Sub_Assertiveness", "Sub_Volatility", "Sub_Withdrawal",
        "Sub_Intellect", "Sub_Openness",
        # Raw Answers (50 cols)
    ]
    for i in range(1, 51):
        headers.append(f"Q{i}")

    writer.writerow(headers)

    for item in assessments:
        row = [
            item.id,
            item.created_at.isoformat() if item.created_at else "",
            item.is_paid,
        ]

        # Parse factors
        try:
            f_scores = json.loads(item.big_five_scores) if item.big_five_scores else {}
            row.extend([
                f_scores.get("extraversion", {}).get("score100", ""),
                f_scores.get("agreeableness", {}).get("score100", ""),
                f_scores.get("conscientiousness", {}).get("score100", ""),
                f_scores.get("neuroticism", {}).get("score100", ""),
                f_scores.get("openness_intellect", {}).get("score100", ""),
            ])
        except Exception:
            row.extend([""] * 5)

        # Parse subfactors
        try:
            s_scores = json.loads(item.sub_factor_scores) if item.sub_factor_scores else {}
            row.extend([
                s_scores.get("compassion", {}).get("score100", ""),
                s_scores.get("politeness", {}).get("score100", ""),
                s_scores.get("industriousness", {}).get("score100", ""),
                s_scores.get("orderliness", {}).get("score100", ""),
                s_scores.get("enthusiasm", {}).get("score100", ""),
                s_scores.get("assertiveness", {}).get("score100", ""),
                s_scores.get("volatility", {}).get("score100", ""),
                s_scores.get("withdrawal", {}).get("score100", ""),
                s_scores.get("intellect", {}).get("score100", ""),
                s_scores.get("openness", {}).get("score100", ""),
            ])
        except Exception:
            row.extend([""] * 10)

        # Parse raw answers
        try:
            answers = json.loads(item.raw_answers) if item.raw_answers else []
            # Fill exactly 50 slots
            while len(answers) < 50:
                answers.append("")
            row.extend(answers[:50])
        except Exception:
            row.extend([""] * 50)

        writer.writerow(row)

    # Return CSV as streaming attachment
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    d_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    response.headers["Content-Disposition"] = f"attachment; filename=eigenknot_results_{d_string}.csv"

    return response
