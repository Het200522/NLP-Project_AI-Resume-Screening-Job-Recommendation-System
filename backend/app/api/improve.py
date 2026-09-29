import json
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.models.analysis import Analysis, AnalysisSkill
from app.services.resume_improver import generate_improved_resume
from app.services.jd_parser import parse_job_description

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["improve"])


@router.get("/{analysis_id}/improve")
async def improve_resume(analysis_id: int, db: Session = Depends(get_db)):
    """
    Generate an improved version of the resume based on the analysis.
    Returns a downloadable PDF with ATS enhancements, missing skills added,
    action verb upgrades, and JD keyword optimization.
    """
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    # Resolve the original PDF path
    original_pdf_path = UPLOAD_DIR / record.resume_filename
    if not original_pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Original resume file not found on disk. Please re-run the analysis.",
        )
    if original_pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Resume improvement is only supported for PDF files.",
        )

    # Check if we have the required data
    if not record.resume_text:
        raise HTTPException(
            status_code=400,
            detail="Original resume text not stored. Please re-run the analysis to enable the improve feature.",
        )
    if not record.jd_text:
        raise HTTPException(
            status_code=400,
            detail="Job description text not stored. Please re-run the analysis to enable the improve feature.",
        )

    # Get skills from database
    skills = db.query(AnalysisSkill).filter(AnalysisSkill.analysis_id == analysis_id).all()
    matched_skills = [s.skill for s in skills if s.status == "matched"]
    missing_skills_list = [s.skill for s in skills if s.status == "missing"]

    # Parse JD to get keywords
    jd_info = parse_job_description(record.jd_text)
    jd_keywords = jd_info.get("keywords", [])

    # Build missing skills list with structure expected by improver
    missing_skills = [{"skill": s} for s in missing_skills_list]

    # Build entities dict
    entities = {
        "name": record.candidate_name,
        "email": record.email,
        "phone": record.phone,
        "location": None,
    }

    # Build sections dict
    sections = {
        "experience": record.experience_text or "Not detected",
        "projects": record.projects_text or "Not detected",
        "education": "Not detected",
        "skills": "",
        "summary": record.summary or "Not detected",
    }

    # Try to extract skills section from resume text
    import re
    skills_match = re.search(
        r"(?:technical\s+)?skills?\s*:?\s*\n(.+?)(?:\n\s*\n|\n(?:education|experience|projects|summary|certifications|technical))",
        record.resume_text, re.IGNORECASE | re.DOTALL,
    )
    if skills_match:
        sections["skills"] = skills_match.group(1).strip()

    # The unified ATS score is the only score; it is stored on the record.
    ats_score = record.final_score

    try:
        result = generate_improved_resume(
            original_pdf_path=original_pdf_path,
            resume_text=record.resume_text,
            entities=entities,
            sections=sections,
            missing_skills=missing_skills,
            matched_skills=matched_skills,
            jd_text=record.jd_text,
            jd_keywords=jd_keywords,
            job_title=record.job_title,
            ats_score=ats_score,
        )
    except Exception as e:
        logger.exception("Failed to generate improved resume")
        raise HTTPException(status_code=500, detail=f"Failed to generate improved resume: {e}") from e

    return FileResponse(
        result["filepath"],
        media_type="application/pdf",
        filename=f"improved_resume_{record.candidate_name or 'candidate'}.pdf",
    )


@router.get("/{analysis_id}/improve/details")
async def get_improve_details(analysis_id: int, db: Session = Depends(get_db)):
    """
    Return the improvement details (what would be changed) without generating the PDF.
    Useful for showing a preview on the frontend.
    """
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    if not record.resume_text or not record.jd_text:
        raise HTTPException(
            status_code=400,
            detail="Original data not stored. Please re-run the analysis.",
        )

    skills = db.query(AnalysisSkill).filter(AnalysisSkill.analysis_id == analysis_id).all()
    missing_skills_list = [s.skill for s in skills if s.status == "missing"]

    jd_info = parse_job_description(record.jd_text)
    jd_keywords = jd_info.get("keywords", [])

    ats_score = record.final_score

    improvements = []
    if missing_skills_list:
        improvements.append(f"Add {len(missing_skills_list)} missing skills: {', '.join(missing_skills_list[:5])}")
    if jd_keywords:
        improvements.append(f"Optimize for {min(len(jd_keywords), 8)} JD keywords")
    improvements.append("Upgrade weak action verbs to strong professional language")
    improvements.append("Enhance professional summary to target the role")
    improvements.append("Ensure ATS-friendly section headings")

    estimated_improvement = min(100.0, ats_score * min(1.3, 1 + len(improvements) * 0.05))

    return {
        "analysis_id": analysis_id,
        "original_ats": round(ats_score, 1),
        "estimated_improved_ats": round(estimated_improvement, 1),
        "improvements": improvements,
        "missing_skills": missing_skills_list,
        "keywords_to_add": jd_keywords[:8],
    }
