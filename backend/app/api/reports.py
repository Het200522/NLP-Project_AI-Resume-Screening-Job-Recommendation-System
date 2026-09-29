import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import Analysis, AnalysisSkill
from app.services.analysis_reader import build_payload
from app.services.report_generator import generate_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["reports"])


@router.get("/{analysis_id}/report")
async def get_report(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    skills = db.query(AnalysisSkill).filter(AnalysisSkill.analysis_id == analysis_id).all()

    try:
        filepath = generate_report(build_payload(record, skills))
    except Exception as e:
        logger.exception("Report generation failed for analysis %s", analysis_id)
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {e}"
        ) from e

    return FileResponse(
        filepath, media_type="application/pdf",
        filename=f"resume_analysis_report_{analysis_id}.pdf",
    )
