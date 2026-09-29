"""
Ties together the full pipeline:
extraction -> preprocessing -> NER -> skill extraction -> JD parsing ->
experience estimation -> similarity scoring -> skill diff -> recommendations
-> summary -> quality/compatibility checks -> persisted Analysis record.
"""
import logging
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import score_to_status
from app.services.resume_parser import extract_text, ExtractionError
from app.services.ner_service import extract_entities
from app.services.skill_extractor import extract_skills, diff_skills
from app.services.jd_parser import parse_job_description
from app.services.similarity_service import compute_final_score
from app.services.experience_service import (
    estimate_years_of_experience,
    experience_match_score,
    parse_experience_requirement,
)
from app.services.recommender import recommend_for_missing_skills
from app.services.summarizer import generate_summary
from app.services.section_extractor import extract_all_sections
from app.services.ats_checker import check_resume_quality, check_compatibility_indicators
from app.services.knockout import evaluate_knockouts
from app.models.analysis import Analysis, AnalysisSkill

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    pass


def run_full_analysis(resume_path: Path, jd_text: str, db: Session | None = None) -> dict:
    try:
        resume_text = extract_text(resume_path)
    except ExtractionError as e:
        raise AnalysisError(str(e)) from e

    if not jd_text or not jd_text.strip():
        raise AnalysisError("Job description text is empty.")

    entities = extract_entities(resume_text)
    resume_skills = extract_skills(resume_text)
    jd_info = parse_job_description(jd_text)
    jd_skills = jd_info["all_skills"]
    sections = extract_all_sections(resume_text)

    diff = diff_skills(
        resume_skills,
        jd_skills,
        required_skills=jd_info["required_skills"],
        preferred_skills=jd_info["preferred_skills"],
    )

    # How much relevant experience the candidate actually has, and how that
    # compares to what this specific role asks for.
    candidate_experience = estimate_years_of_experience(resume_text)
    requirement = parse_experience_requirement(jd_text)
    exp_score = experience_match_score(candidate_experience["years"], requirement)

    scores = compute_final_score(
        resume_text, jd_text,
        total_jd_skills=diff["total_jd_skills"],
        total_matched=diff["total_matched"],
        experience_score=exp_score,
    )
    summary = generate_summary(resume_text, entities, resume_skills)
    # Prioritize hard requirements in the learning plan over "nice to have"s.
    recommendations = recommend_for_missing_skills(
        diff["missing_required"] or diff["missing_skills"]
    )
    quality = check_resume_quality(resume_text, entities, resume_skills)
    compatibility = check_compatibility_indicators(
        resume_text, entities, resume_path.suffix
    )
    # Hard minimums are reported as explicit pass/fail gates. They are
    # deliberately kept out of the score: a candidate who misses one is told
    # exactly what is missing instead of having the number quietly lowered.
    knockouts = evaluate_knockouts(resume_text, jd_text, candidate_experience)
    status = score_to_status(scores["final_score"])

    result = {
        "candidate": entities,
        "job_title": jd_info.get("job_title"),
        "scores": scores,
        "matched_skills": diff["matched_skills"],
        "missing_skills": diff["missing_skills"],
        "additional_skills": diff["additional_skills"],
        "total_jd_skills": diff["total_jd_skills"],
        "required_skills": [s["skill"] for s in jd_info["required_skills"]],
        "preferred_skills": [s["skill"] for s in jd_info["preferred_skills"]],
        "matched_required": diff["matched_required"],
        "missing_required": diff["missing_required"],
        "matched_preferred": diff["matched_preferred"],
        "missing_preferred": diff["missing_preferred"],
        "experience": {
            **candidate_experience,
            "required": requirement.raw if requirement else None,
            "required_min_years": requirement.min_years if requirement else None,
            "required_max_years": requirement.max_years if requirement else None,
            "match_score": exp_score,
        },
        "summary": summary,
        "sections": sections,
        "recommendations": recommendations,
        "quality": quality,
        "compatibility": compatibility,
        "knockouts": knockouts,
        "status": status,
    }

    if db is not None:
        record = Analysis(
            candidate_name=entities.get("name"),
            email=entities.get("email"),
            phone=entities.get("phone"),
            resume_filename=resume_path.name,
            job_title=jd_info.get("job_title"),
            semantic_score=scores["semantic_score"],
            skill_score=scores["skill_score"],
            keyword_score=scores["keyword_score"],
            final_score=scores["final_score"],
            summary=summary,
            experience_text=sections.get("experience"),
            projects_text=sections.get("projects"),
            quality_json=json.dumps(quality),
            compatibility_json=json.dumps(compatibility),
            resume_text=resume_text[:10000],  # store for improve feature
            jd_text=jd_text[:10000],          # store for improve feature
            status=status,
        )
        db.add(record)
        db.flush()  # get record.id before commit

        for skill in diff["matched_skills"]:
            db.add(AnalysisSkill(analysis_id=record.id, skill=skill, status="matched"))
        for skill in diff["missing_skills"]:
            db.add(AnalysisSkill(analysis_id=record.id, skill=skill, status="missing"))
        for skill in diff["additional_skills"]:
            db.add(AnalysisSkill(analysis_id=record.id, skill=skill, status="additional"))

        db.commit()
        db.refresh(record)
        result["id"] = record.id
        result["created_at"] = record.created_at

    return result
