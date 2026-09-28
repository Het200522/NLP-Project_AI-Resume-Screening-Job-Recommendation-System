import logging

from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.file_utils import save_upload
from app.services.analysis_orchestrator import run_full_analysis, AnalysisError
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisListItem, BulkCandidateResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("", response_model=list[AnalysisListItem])
async def list_candidates(db: Session = Depends(get_db)):
    records = db.query(Analysis).order_by(Analysis.final_score.desc()).all()
    return records


@router.post("/bulk-analyze", response_model=list[BulkCandidateResult])
async def bulk_analyze(
    resumes: list[UploadFile] = File(...),
    job_description: str = Form(...),
    db: Session = Depends(get_db),
):
    results = []
    for resume in resumes:
        try:
            dest = await save_upload(resume, kind="resume")
            analysis = run_full_analysis(dest, job_description, db=db)
            results.append({
                "filename": resume.filename,
                "candidate_name": analysis["candidate"].get("name"),
                "final_score": analysis["scores"]["final_score"],
                "skills_matched": len(analysis["matched_skills"]),
                "missing_skills": len(analysis["missing_skills"]),
                "status": analysis["status"],
                "error": None,
            })
        except AnalysisError as e:
            results.append({
                "filename": resume.filename, "candidate_name": None, "final_score": 0,
                "skills_matched": 0, "missing_skills": 0, "status": "Error", "error": str(e),
            })
        except Exception as e:
            logger.exception("Bulk analyze failed for %s", resume.filename)
            results.append({
                "filename": resume.filename, "candidate_name": None, "final_score": 0,
                "skills_matched": 0, "missing_skills": 0, "status": "Error",
                "error": "Internal error during analysis.",
            })

    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results
