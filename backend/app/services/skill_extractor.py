"""
Skill extraction: loads backend/data/skills.csv and matches skills against
resume/JD text using whole-word / phrase matching (never naive substring
matching, to avoid false positives like "R" matching inside "Learning").
"""
import csv
import re
import logging
from dataclasses import dataclass
from functools import lru_cache

from app.config import DATA_DIR

logger = logging.getLogger(__name__)


@dataclass
class SkillEntry:
    canonical: str
    category: str
    patterns: list[re.Pattern]


@lru_cache(maxsize=1)
def _load_skills() -> list[SkillEntry]:
    skills_path = DATA_DIR / "skills.csv"
    entries: list[SkillEntry] = []

    if not skills_path.exists():
        logger.warning("skills.csv not found at %s", skills_path)
        return entries

    with open(skills_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            canonical = row["skill"].strip()
            category = row.get("category", "").strip() or "General"
            alias_field = (row.get("aliases") or "").strip()
            variants = [canonical] + [a.strip() for a in alias_field.split("|") if a.strip()]

            patterns = []
            for variant in variants:
                escaped = re.escape(variant)
                # Match as a whole word/phrase, allowing surrounding punctuation.
                pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
                patterns.append(pattern)

            entries.append(SkillEntry(canonical=canonical, category=category, patterns=patterns))

    return entries


def extract_skills(text: str) -> list[dict]:
    """
    Returns a list of {"skill": str, "category": str} for every skill found
    in the text, deduplicated by canonical name.
    """
    if not text:
        return []

    skills = _load_skills()
    found = {}

    for entry in skills:
        for pattern in entry.patterns:
            if pattern.search(text):
                found[entry.canonical] = entry.category
                break

    return [{"skill": k, "category": v} for k, v in sorted(found.items())]


def diff_skills(resume_skills: list[dict], jd_skills: list[dict]) -> dict:
    """
    Compares resume skills against JD-required skills.
    Returns matched, missing, and additional (resume-only) skills.
    """
    resume_names = {s["skill"] for s in resume_skills}
    jd_names = {s["skill"] for s in jd_skills}

    matched = sorted(resume_names & jd_names)
    missing = sorted(jd_names - resume_names)
    additional = sorted(resume_names - jd_names)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "additional_skills": additional,
        "total_jd_skills": len(jd_names),
        "total_matched": len(matched),
        "total_missing": len(missing),
    }
