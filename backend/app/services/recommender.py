"""
recommender.py
Given a list of missing skills, recommend learning topics, levels, and
project ideas from a local dataset (no paid APIs required).
"""
import csv
import logging
from functools import lru_cache

from app.config import DATA_DIR

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_recommendations() -> dict[str, dict]:
    path = DATA_DIR / "course_recommendations.csv"
    data = {}
    if not path.exists():
        logger.warning("course_recommendations.csv not found at %s", path)
        return data

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            skill = row["skill"].strip()
            data[skill.lower()] = {
                "skill": skill,
                "level": row.get("level", "").strip(),
                "topics": [t.strip() for t in (row.get("topics") or "").split("|") if t.strip()],
                "project_idea": row.get("project_idea", "").strip(),
                "resource_hint": row.get("resource_hint", "").strip(),
            }
    return data


def recommend_for_missing_skills(missing_skills: list[str]) -> list[dict]:
    """
    Returns a recommendation card per missing skill. Skills without a
    dataset entry still get a generic recommendation rather than being
    silently dropped.
    """
    catalog = _load_recommendations()
    recommendations = []

    for skill in missing_skills:
        entry = catalog.get(skill.lower())
        if entry:
            recommendations.append(entry)
        else:
            recommendations.append({
                "skill": skill,
                "level": "Beginner",
                "topics": [f"Fundamentals of {skill}", f"Hands-on practice with {skill}"],
                "project_idea": f"Build a small project that applies {skill} in context.",
                "resource_hint": "Search official documentation and reputable free courses.",
            })

    return recommendations
