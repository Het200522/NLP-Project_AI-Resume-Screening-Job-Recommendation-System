import json
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.file_utils import save_upload
from app.services.analysis_orchestrator import run_full_analysis, AnalysisError
from app.services.recommender import recommend_for_missing_skills
from app.models.analysis import Analysis, AnalysisSkill
from app.schemas.analysis import AnalyzeResponse, AnalysisListItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    db: Session = Depends(get_db),
):
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    dest = await save_upload(resume, kind="resume")

    try:
        result = run_full_analysis(dest, job_description, db=db)
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        logger.exception("Unexpected error during analysis")
        raise HTTPException(status_code=500, detail="Analysis failed due to an internal error.")

    return result


@router.get("/analysis/{analysis_id}", response_model=AnalyzeResponse)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    skills = db.query(AnalysisSkill).filter(AnalysisSkill.analysis_id == analysis_id).all()
    matched = [s.skill for s in skills if s.status == "matched"]
    missing = [s.skill for s in skills if s.status == "missing"]
    additional = [s.skill for s in skills if s.status == "additional"]

    try:
        quality = json.loads(record.quality_json) if record.quality_json else {}
    except json.JSONDecodeError:
        quality = {}
    try:
        compatibility = json.loads(record.compatibility_json) if record.compatibility_json else {}
    except json.JSONDecodeError:
        compatibility = {}

    return {
        "id": record.id,
        "candidate": {
            "name": record.candidate_name, "email": record.email, "phone": record.phone,
            "location": None, "linkedin": None, "github": None, "organizations": [],
        },
        "job_title": record.job_title,
        "scores": {
            "semantic_score": record.semantic_score,
            "tfidf_score": record.semantic_score,
            "skill_score": record.skill_score,
            "keyword_score": record.keyword_score,
            "final_score": record.final_score,
            "used_semantic_model": True,
            "weights": {},
        },
        "matched_skills": matched,
        "missing_skills": missing,
        "additional_skills": additional,
        "total_jd_skills": len(matched) + len(missing),
        "summary": record.summary or "Not detected",
        "sections": {
            "experience": record.experience_text or "Not detected",
            "projects": record.projects_text or "Not detected",
            "education": "Not detected",
            "certifications": "Not detected",
        },
        "recommendations": recommend_for_missing_skills(missing),
        "quality": quality,
        "compatibility": compatibility,
        "status": record.status or "",
        "created_at": record.created_at,
    }


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    db.delete(record)
    db.commit()
    return {"deleted": True, "id": analysis_id}
