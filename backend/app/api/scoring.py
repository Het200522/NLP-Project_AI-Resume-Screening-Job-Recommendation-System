"""
Exposes the live scoring configuration.

The settings page previously hardcoded a weight table that had already been
deleted from the backend, so the UI quietly described a model that no longer
existed. Reading it from config here means one source of truth.
"""
from fastapi import APIRouter

from app.config import (
    ATS_WEIGHTS,
    PARSEABILITY_WEIGHTS,
    SEMANTIC_FLOOR,
    SEMANTIC_CEILING,
)

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


@router.get("/config")
def scoring_config() -> dict:
    return {
        "weights": dict(ATS_WEIGHTS),
        "parseability_weights": dict(PARSEABILITY_WEIGHTS),
        "semantic_floor": SEMANTIC_FLOOR,
        "semantic_ceiling": SEMANTIC_CEILING,
        "formula": (
            "Final Score = Σ (weight × category_score), renormalized across "
            "the categories that could be evaluated for this role."
        ),
        "knockouts_note": (
            "Hard requirements stated by the job description are evaluated as "
            "pass/fail gates and are not part of the score."
        ),
    }
