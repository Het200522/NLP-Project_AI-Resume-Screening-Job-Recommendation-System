"""
similarity_service.py

Implements:
  - TF-IDF + cosine similarity (baseline)
  - Sentence-transformer semantic similarity (all-MiniLM-L6-v2 by default)
  - Skill-match score
  - Keyword overlap score
  - Combined final score using configurable weights (app.config)
"""
import logging
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import (
    SENTENCE_TRANSFORMER_MODEL, ENABLE_SEMANTIC_MODEL,
    ATS_WEIGHTS,
)
from app.services.preprocess import preprocess_for_matching

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_semantic_model():
    if not ENABLE_SEMANTIC_MODEL:
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
    except Exception as e:
        logger.warning(
            "sentence-transformers model unavailable (%s). "
            "Falling back to TF-IDF-only scoring for semantic score.",
            e,
        )
        return None


def tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """Returns 0-100 TF-IDF cosine similarity score."""
    resume_clean = preprocess_for_matching(resume_text)
    jd_clean = preprocess_for_matching(jd_text)

    if not resume_clean.strip() or not jd_clean.strip():
        return 0.0

    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_clean, jd_clean])
    except ValueError:
        return 0.0

    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(float(score) * 100, 2)


def semantic_similarity(resume_text: str, jd_text: str) -> float | None:
    """
    Returns 0-100 semantic similarity score using sentence embeddings,
    or None if the model could not be loaded (caller should fall back
    to the TF-IDF score in that case).
    """
    model = _load_semantic_model()
    if model is None:
        return None

    if not resume_text.strip() or not jd_text.strip():
        return 0.0

    embeddings = model.encode([resume_text[:5000], jd_text[:5000]])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    # Clamp: cosine on embeddings can be slightly negative for unrelated text.
    score = max(0.0, min(1.0, float(score)))
    return round(score * 100, 2)


def skill_match_score(total_jd_skills: int, total_matched: int) -> float:
    if total_jd_skills == 0:
        return 0.0
    return round((total_matched / total_jd_skills) * 100, 2)


def keyword_overlap_score(resume_text: str, jd_text: str, top_n: int = 30) -> float:
    """
    Extracts the JD's top-N TF-IDF keywords and measures what fraction of
    them appear in the resume text (simple, explainable keyword coverage).
    """
    jd_clean = preprocess_for_matching(jd_text)
    resume_clean = preprocess_for_matching(resume_text)

    if not jd_clean.strip():
        return 0.0

    vectorizer = TfidfVectorizer(max_features=top_n)
    try:
        vectorizer.fit([jd_clean])
    except ValueError:
        return 0.0

    keywords = set(vectorizer.get_feature_names_out())
    if not keywords:
        return 0.0

    resume_tokens = set(resume_clean.split())
    overlap = keywords & resume_tokens
    return round((len(overlap) / len(keywords)) * 100, 2)


def compute_final_score(
    resume_text: str,
    jd_text: str,
    total_jd_skills: int,
    total_matched: int,
) -> dict:
    """
    Computes a real-world ATS score using 7 weighted categories modeled
    after how commercial ATS systems (Workday, Taleo, Greenhouse, iCIMS)
    are publicly known to rank candidates.

    Final Score = Σ (weight_i × category_score_i)

    Categories and default weights:
      keyword_match     30%  — JD keywords found in resume
      skill_match       25%  — Required skills matched
      semantic_match    15%  — Sentence-embedding similarity
      contact_info      10%  — Name, email, phone, LinkedIn, GitHub
      section_structure 10%  — Standard resume sections present
      achievements       5%  — Quantifiable metrics (numbers, %, $)
      action_verbs       5%  — Strong action verb usage

    Returns scores in the 0-100 range, each rounded to 2 decimals.
    """
    tfidf_score = tfidf_similarity(resume_text, jd_text)
    semantic_score = semantic_similarity(resume_text, jd_text)
    used_semantic = semantic_score is not None
    if semantic_score is None:
        semantic_score = tfidf_score

    skill_score = skill_match_score(total_jd_skills, total_matched)
    keyword_score = keyword_overlap_score(resume_text, jd_text)

    # --- Individual category scores (all 0-100) ---
    categories = {
        "keyword_match": keyword_score,
        "skill_match": skill_score,
        "semantic_match": semantic_score,
        "contact_info": _contact_score(resume_text),
        "section_structure": _section_score(resume_text),
        "achievements": _achievements_score(resume_text),
        "action_verbs": _verb_score(resume_text),
    }

    # --- Weighted final score ---
    final_score = sum(
        ATS_WEIGHTS[cat] * score for cat, score in categories.items()
    )
    final_score = round(max(0.0, min(100.0, final_score)), 2)

    return {
        "semantic_score": semantic_score,
        "tfidf_score": tfidf_score,
        "skill_score": skill_score,
        "keyword_score": keyword_score,
        "final_score": final_score,
        "used_semantic_model": used_semantic,
        "categories": {cat: round(score, 2) for cat, score in categories.items()},
        "weights": dict(ATS_WEIGHTS),
    }


def _contact_score(resume_text: str) -> float:
    """0-100: fraction of key contact fields detected."""
    import re
    checks = {
        "email": bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text)),
        "phone": bool(re.search(r"[\+]?[(]?\d{1,4}[)]?[-\s./]?\d{1,4}[-\s./]?\d{1,9}", resume_text)),
        "linkedin": bool(re.search(r"linkedin\.com", resume_text, re.IGNORECASE)),
        "github": bool(re.search(r"github\.com", resume_text, re.IGNORECASE)),
    }
    return round((sum(checks.values()) / len(checks)) * 100, 2)


def _section_score(resume_text: str) -> float:
    """0-100: fraction of core resume sections detected."""
    import re
    lower = resume_text.lower()
    core_sections = ["experience", "education", "skills", "projects"]
    found = sum(
        1 for s in core_sections
        if re.search(rf"\b{re.escape(s)}\b", lower)
    )
    return round(min(100.0, (found / 3) * 100), 2)


def _achievements_score(resume_text: str) -> float:
    """0-100: density of quantifiable achievement indicators."""
    import re
    matches = re.findall(
        r"(\$\s?\d[\d,]*|\d+(\.\d+)?\s?%|\b\d+x\b|\b\d{2,}\+?\b)",
        resume_text,
    )
    count = len(matches)
    return round(min(100.0, (count / 5) * 100), 2)


def _verb_score(resume_text: str) -> float:
    """0-100: fraction of content lines starting with a strong action verb."""
    ACTION_VERBS = {
        "achieved", "built", "created", "designed", "developed", "engineered",
        "established", "executed", "implemented", "improved", "increased",
        "initiated", "launched", "led", "managed", "optimized", "organized",
        "reduced", "researched", "resolved", "spearheaded", "streamlined",
        "supervised", "trained", "transformed", "delivered", "automated",
        "architected", "analyzed", "collaborated", "coordinated", "deployed",
    }
    line_starts = []
    for line in resume_text.splitlines():
        stripped = line.strip().lstrip("-•●▪◦‣*").strip()
        if not stripped:
            continue
        words = stripped.split()
        if words:
            line_starts.append(words[0].lower().strip(".,:;"))
    total = max(1, len(line_starts))
    verb_count = sum(1 for w in line_starts if w in ACTION_VERBS)
    ratio = verb_count / total
    return round(min(100.0, ratio * 300), 2)
