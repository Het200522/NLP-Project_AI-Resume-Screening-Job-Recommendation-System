"""
analysis_reader.py
Rebuilds a full analysis payload from a persisted Analysis record.

The per-tier skill split, the experience estimate and the score-category
breakdown are derived rather than stored, so they are recomputed here from
the resume/JD text kept on the row. This keeps previously saved analyses
readable without a schema migration.
"""
import json

from app.config import ATS_WEIGHTS, SEMANTIC_FLOOR, SEMANTIC_CEILING
from app.services.jd_parser import parse_job_description
from app.services.similarity_service import (
    tfidf_similarity,
    parseability_score,
)
from app.services.experience_service import (
    estimate_years_of_experience,
    experience_match_score,
    parse_experience_requirement,
)
from app.services.knockout import evaluate_knockouts
from app.services.recommender import recommend_for_missing_skills


def _load_json(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def build_experience(record) -> dict:
    """Experience estimate for a stored record, or a clear placeholder."""
    if not record.resume_text or not record.jd_text:
        return {
            "years": 0.0,
            "source": "unavailable",
            "detail": "Experience could not be determined for this record.",
            "required": None,
            "required_min_years": None,
            "required_max_years": None,
            "match_score": None,
        }

    estimate = estimate_years_of_experience(record.resume_text)
    requirement = parse_experience_requirement(record.jd_text)
    score = experience_match_score(estimate["years"], requirement)
    return {
        **estimate,
        "required": requirement.raw if requirement else None,
        "required_min_years": requirement.min_years if requirement else None,
        "required_max_years": requirement.max_years if requirement else None,
        "match_score": score,
    }


def build_tiered_skills(record, matched: list[str], missing: list[str]) -> dict:
    """Splits stored skill rows into the role's required vs. preferred tiers."""
    required_names: set[str] = set()
    preferred_names: set[str] = set()

    if record.jd_text:
        jd_info = parse_job_description(record.jd_text)
        required_names = {s["skill"] for s in jd_info["required_skills"]}
        preferred_names = {s["skill"] for s in jd_info["preferred_skills"]}

    matched_set = set(matched)
    missing_set = set(missing)
    return {
        "required_skills": sorted(required_names),
        "preferred_skills": sorted(preferred_names),
        "matched_required": sorted(matched_set & required_names),
        "missing_required": sorted(missing_set & required_names),
        "matched_preferred": sorted(matched_set & preferred_names),
        "missing_preferred": sorted(missing_set & preferred_names),
    }


def _uncalibrate_semantic(score: float) -> float:
    """
    Inverts the semantic calibration so a stored score can be reported on the
    same uncalibrated 0-100 scale the live endpoint returns. Scores clipped
    at either end of the band are reported at that end rather than guessed.
    """
    if score <= 0:
        return SEMANTIC_FLOOR
    if score >= 100:
        return SEMANTIC_CEILING
    return round(
        SEMANTIC_FLOOR + score / 100.0 * (SEMANTIC_CEILING - SEMANTIC_FLOOR), 2
    )


def build_scores(record, experience: dict) -> dict:
    """
    Rebuilds the score payload for a stored record.

    TF-IDF is cheap and deterministic, so it is recomputed from the stored text
    instead of being aliased to the semantic score. Whether the embedding model
    ran is inferred by comparing the stored semantic score against that TF-IDF
    value: when the model was unavailable at analysis time the two are identical
    by construction.

    The category breakdown is also restored. Every category is either stored on
    the row (skill, keyword, semantic) or derived from text the row keeps
    (experience, parseability), so a saved analysis shows the same sub-scores
    the live endpoint returned rather than an empty breakdown.
    """
    tfidf = tfidf_similarity(record.resume_text or "", record.jd_text or "")
    stored_semantic = record.semantic_score
    used_model = abs(stored_semantic - tfidf) > 0.01
    parseability, parseability_detail = parseability_score(record.resume_text or "")
    exp_score = experience.get("match_score")

    categories = {
        "skill_match": round(record.skill_score, 2),
        "keyword_match": round(record.keyword_score, 2),
        "semantic_match": round(stored_semantic, 2),
        "experience_match": None if exp_score is None else round(exp_score, 2),
        "parseability": parseability,
    }

    return {
        "semantic_score": stored_semantic,
        "tfidf_score": tfidf,
        "skill_score": record.skill_score,
        "keyword_score": record.keyword_score,
        "final_score": record.final_score,
        "used_semantic_model": used_model,
        "raw_semantic_score": _uncalibrate_semantic(stored_semantic) if used_model else None,
        "experience_score": exp_score,
        "parseability_score": parseability,
        "categories": categories,
        "weights": dict(ATS_WEIGHTS),
        "keyword_detail": {},
        "parseability_detail": parseability_detail,
    }


def build_payload(record, skills) -> dict:
    """
    Assembles the full analysis payload from a record plus its AnalysisSkill
    rows. `skills` is a list of rows with `.skill` and `.status` attributes.
    """
    matched = [s.skill for s in skills if s.status == "matched"]
    missing = [s.skill for s in skills if s.status == "missing"]
    additional = [s.skill for s in skills if s.status == "additional"]

    experience = build_experience(record)
    tiers = build_tiered_skills(record, matched, missing)
    knockouts = (
        evaluate_knockouts(record.resume_text, record.jd_text, experience)
        if record.resume_text and record.jd_text
        else {"gates": [], "failed": [], "passed": True, "evaluated": False}
    )

    return {
        "id": record.id,
        "candidate": {
            "name": record.candidate_name,
            "email": record.email,
            "phone": record.phone,
            "location": None,
            "linkedin": None,
            "github": None,
            "organizations": [],
        },
        "job_title": record.job_title,
        "scores": build_scores(record, experience),
        "matched_skills": matched,
        "missing_skills": missing,
        "additional_skills": additional,
        "total_jd_skills": len(matched) + len(missing),
        **tiers,
        "experience": experience,
        "summary": record.summary or "Not detected",
        "sections": {
            "experience": record.experience_text or "Not detected",
            "projects": record.projects_text or "Not detected",
            "education": "Not detected",
            "certifications": "Not detected",
        },
        "recommendations": recommend_for_missing_skills(
            tiers["missing_required"] or missing
        ),
        "quality": _load_json(record.quality_json),
        "compatibility": _load_json(record.compatibility_json),
        "knockouts": knockouts,
        "status": record.status or "",
        "created_at": record.created_at,
        # Flattened fields the PDF report reads.
        "experience_text": record.experience_text or "Not detected",
        "projects_text": record.projects_text or "Not detected",
    }
