"""
jd_parser.py
Extracts structured information from a job description: title, required
skills, preferred skills, education/experience requirements, and top keywords.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.skill_extractor import extract_skills
from app.services.preprocess import preprocess_for_matching
from app.services.experience_service import parse_experience_requirement


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


# A line that *begins* with a "nice to have" marker and is short enough to be
# a heading or a one-line list item, e.g. "Preferred Skills:" or
# "Bonus points: AWS certification". Must start the line so that a required
# bullet mentioning "preferably" mid-sentence is not misread as a boundary.
_PREFERRED_MARKER = re.compile(
    r"^[^\S\n]*(?:preferred|preferably|nice to have|good to have|nice-to-have|"
    r"good-to-have|bonus|desirable|ideally|optional|is a plus|are a plus)"
    r"[^\n]{0,70}$",
    re.IGNORECASE | re.MULTILINE,
)


def _split_required_preferred(jd_text: str) -> tuple[str, str]:
    """
    Splits a JD into a required section and a preferred section at the first
    "nice to have" boundary. If no boundary exists, the whole JD is required
    -- which is the conservative reading, since a skill we cannot prove is
    optional should be treated as expected.
    """
    match = _PREFERRED_MARKER.search(jd_text)
    if not match:
        return jd_text, ""

    required_text = jd_text[: match.start()]
    preferred_text = jd_text[match.end():]
    if not preferred_text.strip():
        return required_text, ""
    return required_text, preferred_text


def parse_job_description(jd_text: str) -> dict:
    skills = extract_skills(jd_text)

    required_section, preferred_section = _split_required_preferred(jd_text)

    required_skill_names = {s["skill"] for s in extract_skills(required_section)}
    preferred_skill_names = {s["skill"] for s in extract_skills(preferred_section)}
    preferred_skill_names -= required_skill_names

    required_skills = [s for s in skills if s["skill"] in required_skill_names]
    preferred_skills = [s for s in skills if s["skill"] in preferred_skill_names]

    # If the split found nothing on the required side (unstructured JD), the
    # "nice to have" skills are the only thing we can positively identify, so
    # the rest stand in as requirements.
    if not required_skills and preferred_skills:
        required_skills = [s for s in skills if s["skill"] not in preferred_skill_names]

    experience = parse_experience_requirement(jd_text)

    return {
        "job_title": _guess_title(jd_text),
        "required_skills": required_skills or skills,
        "preferred_skills": preferred_skills,
        "all_skills": skills,
        "education_requirement": _extract_education(jd_text),
        "experience_requirement": _extract_experience(jd_text),
        "experience_min_years": experience.min_years if experience else None,
        "experience_max_years": experience.max_years if experience else None,
        "keywords": _top_keywords(jd_text),
    }
