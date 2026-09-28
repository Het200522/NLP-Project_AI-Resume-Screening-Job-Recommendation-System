"""
jd_parser.py
Extracts structured information from a job description: title, required
skills, education/experience requirements, and top keywords.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.skill_extractor import extract_skills
from app.services.preprocess import preprocess_for_matching


def _guess_title(jd_text: str) -> str | None:
    m = re.search(r"(?:job title|position|role)\s*[:\-]\s*(.+)", jd_text, re.IGNORECASE)
    if m:
        return m.group(1).strip().split("\n")[0].strip()

    lines = [l.strip() for l in jd_text.splitlines() if l.strip()]
    if not lines:
        return None
    first = lines[0]
    if len(first.split()) <= 8 and not first.endswith("."):
        return first
    return None


def _extract_experience(jd_text: str) -> str | None:
    m = re.search(r"(\d+\+?\s*(?:-|to)?\s*\d*\s*years?)\s+(?:of\s+)?experience", jd_text, re.IGNORECASE)
    return m.group(0) if m else None


def _extract_education(jd_text: str) -> str | None:
    m = re.search(
        r"(bachelor'?s?|master'?s?|b\.?tech|m\.?tech|b\.?sc|m\.?sc|phd|degree)[^.\n]{0,80}",
        jd_text, re.IGNORECASE,
    )
    return m.group(0).strip() if m else None


def _top_keywords(jd_text: str, n: int = 15) -> list[str]:
    cleaned = preprocess_for_matching(jd_text)
    if not cleaned.strip():
        return []
    vectorizer = TfidfVectorizer(max_features=n)
    try:
        vectorizer.fit([cleaned])
    except ValueError:
        return []
    return list(vectorizer.get_feature_names_out())


def parse_job_description(jd_text: str) -> dict:
    skills = extract_skills(jd_text)

    # Heuristic split: skills mentioned near "required"/"must have" vs
    # "preferred"/"nice to have". Falls back to all-required if unclear.
    required_section = jd_text
    preferred_section = ""
    m = re.search(r"(preferred|nice to have|good to have)[:\s]", jd_text, re.IGNORECASE)
    if m:
        required_section = jd_text[: m.start()]
        preferred_section = jd_text[m.start():]

    required_skills = extract_skills(required_section)
    preferred_skill_names = {s["skill"] for s in extract_skills(preferred_section)}
    required_skill_names = {s["skill"] for s in required_skills}
    preferred_skills = [s for s in skills if s["skill"] in preferred_skill_names and s["skill"] not in required_skill_names]

    return {
        "job_title": _guess_title(jd_text),
        "required_skills": [s for s in skills if s["skill"] in required_skill_names] or skills,
        "preferred_skills": preferred_skills,
        "all_skills": skills,
        "education_requirement": _extract_education(jd_text),
        "experience_requirement": _extract_experience(jd_text),
        "keywords": _top_keywords(jd_text),
    }
