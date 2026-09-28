import json

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import Analysis, AnalysisSkill
from app.services.report_generator import generate_report
from app.services.recommender import recommend_for_missing_skills

router = APIRouter(prefix="/api/analysis", tags=["reports"])


@router.get("/{analysis_id}/report")
async def get_report(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    skills = db.query(AnalysisSkill).filter(AnalysisSkill.analysis_id == analysis_id).all()
    matched = [s.skill for s in skills if s.status == "matched"]
    missing = [s.skill for s in skills if s.status == "missing"]

    try:
        quality = json.loads(record.quality_json) if record.quality_json else {}
    except json.JSONDecodeError:
        quality = {}
    try:
        compatibility = json.loads(record.compatibility_json) if record.compatibility_json else {}
    except json.JSONDecodeError:
        compatibility = {}

    try:
        filepath = generate_report({
            "id": record.id,
            "candidate": {"name": record.candidate_name, "email": record.email, "phone": record.phone},
            "job_title": record.job_title,
            "scores": {
                "final_score": record.final_score,
                "semantic_score": record.semantic_score,
                "skill_score": record.skill_score,
                "keyword_score": record.keyword_score,
            },
            "matched_skills": matched,
            "missing_skills": missing,
            "recommendations": recommend_for_missing_skills(missing),
            "summary": record.summary,
            "experience_text": record.experience_text,
            "projects_text": record.projects_text,
            "quality": quality,
            "compatibility": compatibility,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}") from e

    return FileResponse(
        filepath, media_type="application/pdf",
        filename=f"resume_analysis_report_{analysis_id}.pdf",
    )
