"""
similarity_service.py

The single, unified ATS scoring engine. Everything a candidate is ranked on
is computed here so there is exactly one score and one set of sub-scores.

  - Requirement coverage: JD skills present, JD keywords present (with
    synonym and fuzzy matching), embedding similarity, experience fit
  - Parseability: whether the resume is legible to a parser at all
  - Weighted combination per app.config.ATS_WEIGHTS

Hard minimums the job description states (years, degree, certifications) are
handled separately by app.services.knockout as explicit gates, so a failed
minimum is explained rather than silently averaged into the number.
"""
import logging
import re
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import (
    SENTENCE_TRANSFORMER_MODEL, ENABLE_SEMANTIC_MODEL,
    ATS_WEIGHTS, PARSEABILITY_WEIGHTS,
    SEMANTIC_FLOOR, SEMANTIC_CEILING,
)
from app.services.preprocess import preprocess_for_matching
from app.services.keyword_matcher import (
    fuzzy_find,
    tokenize_for_matching,
)
from app.services.ats_checker import _formatting_risk_score, _length_structure_score

logger = logging.getLogger(__name__)

# Guard on fuzzy comparisons so a very long resume cannot make scoring slow.
_MAX_FUZZY_COMPARISONS = 2000


@lru_cache(maxsize=1)
def _background_corpus() -> list[str]:
    """
    A domain background corpus used to give IDF real meaning.

    Fitting TF-IDF on only a resume and a JD yields two documents, where
    every term gets an identical IDF and the score collapses to raw term
    frequency (shared terms end up weighted the same as unique ones). The
    built-in role descriptions give us a real corpus, so a term that appears
    in every job posting ("experience", "skills", "team") is correctly
    discounted while a role-specific term ("siem", "terraform") is not.
    """
    from app.services.role_templates import ROLES

    corpus = [preprocess_for_matching(r["description"]) for r in ROLES.values()]
    return [c for c in corpus if c.strip()]


def _normalize_token(token: str) -> str:
    """
    Strips punctuation that survives tokenization so that the same term
    matches across documents.

    preprocess_for_matching deliberately keeps '.' and '-' inside a token
    (so "node.js" and "3.5" survive), but that leaves trailing sentence
    punctuation attached: "with SIEM." yields "siem." while a resume
    mentioning "SIEM" yields "siem", and the two never match.
    """
    return token.strip(".-")


@lru_cache(maxsize=1)
def _background_idf() -> dict[str, float]:
    """Term -> IDF weight, measured against the role-description corpus."""
    corpus = _background_corpus()
    if not corpus:
        return {}
    vectorizer = TfidfVectorizer()
    try:
        vectorizer.fit_transform(corpus)
    except ValueError:
        return {}
    return {
        term: float(idf)
        for term, idf in zip(vectorizer.get_feature_names_out(), vectorizer.idf_)
    }


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


def _calibrate_semantic(score: float) -> float:
    """
    Sentence embeddings compress all professional text into a narrow band: two
    completely unrelated documents still sit at 0.35-0.50, and a genuinely
    aligned pair rarely exceeds ~0.75. Rescale the usable band onto 0-100 so
    an unrelated candidate scores near zero and a strong match is not capped
    at the bottom of the range.
    """
    if score is None:
        return 0.0
    floor, ceiling = SEMANTIC_FLOOR, SEMANTIC_CEILING
    if ceiling <= floor:
        return round(max(0.0, min(100.0, score)), 2)
    scaled = (score - floor) / (ceiling - floor) * 100.0
    return round(max(0.0, min(100.0, scaled)), 2)


def tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """Returns 0-100 TF-IDF cosine similarity score."""
    resume_clean = preprocess_for_matching(resume_text)
    jd_clean = preprocess_for_matching(jd_text)

    if not resume_clean.strip() or not jd_clean.strip():
        return 0.0

    # Fit on the background corpus plus both documents so IDF reflects how
    # common a term is across job postings, not just "it occurred twice".
    corpus = _background_corpus()
    vectorizer = TfidfVectorizer()
    try:
        vectorizer.fit_transform(corpus)
        tfidf_matrix = vectorizer.transform([resume_clean, jd_clean])
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
    """
    0-100 ATS skill match: the share of the job description's skills that
    appear in the resume. Every JD skill counts the same, which is how
    commercial ATS keyword matching works.
    """
    if not total_jd_skills:
        return 0.0
    return round(min(total_matched, total_jd_skills) / total_jd_skills * 100, 2)


def keyword_overlap_score(
    resume_text: str,
    jd_text: str,
    top_n: int = 40,
    *,
    return_detail: bool = False,
):
    """
    Extracts the JD's most distinctive terms and measures what fraction of
    their *weighted* mass the resume covers.

    Weights come from the background job-description corpus, so filler that
    appears in every posting ("experience", "skills", "best", "knowledge")
    is worth far less than a role-specific term ("siem", "kubernetes").

    Matching is synonym-aware and fuzzy-tolerant, the way commercial ATS
    keyword search is: "k8s" satisfies "kubernetes", and a near-spelling
    ("kubernets") still counts. Without this a candidate loses real match
    points for using the term their industry actually uses.
    """
    jd_clean = preprocess_for_matching(jd_text)
    resume_clean = preprocess_for_matching(resume_text)

    if not jd_clean.strip():
        return (0.0, {}) if return_detail else 0.0

    idf = _background_idf()
    if not idf:
        return (0.0, {}) if return_detail else 0.0

    # Rank the JD's terms by how *specific* they are (high IDF x frequency),
    # not by raw frequency, then keep the most distinctive ones.
    counts: dict[str, int] = {}
    for token in jd_clean.split():
        token = _normalize_token(token)
        if token:
            counts[token] = counts.get(token, 0) + 1

    weights = {
        token: idf.get(token, 0.0) * (1 + 0.15 * (count - 1))
        for token, count in counts.items()
    }
    ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    keywords = {token for token, _ in ranked if weights[token] > 0}

    if not keywords:
        return (0.0, {}) if return_detail else 0.0

    resume_tokens = tokenize_for_matching(resume_clean)
    budget = [_MAX_FUZZY_COMPARISONS]

    exact = {t for t in keywords if t in resume_tokens}
    fuzzy = fuzzy_find(keywords - exact, resume_tokens, budget=budget)

    total_weight = sum(weights[t] for t in keywords)
    if total_weight <= 0:
        return (0.0, {}) if return_detail else 0.0

    hit_weight = sum(weights[t] for t in exact | fuzzy)
    score = round((hit_weight / total_weight) * 100, 2)

    if return_detail:
        return score, {
            "keywords": sorted(keywords),
            "matched": sorted(exact | fuzzy),
            "missing": sorted(keywords - exact - fuzzy),
            "fuzzy_matches": sorted(fuzzy),
        }
    return score


def compute_final_score(
    resume_text: str,
    jd_text: str,
    total_jd_skills: int,
    total_matched: int,
    *,
    experience_score: float | None = None,
) -> dict:
    """
    The single, unified ATS score.

    Requirement coverage dominates, because that is what a commercial ATS
    ranks on, and because it is the only part of the score that changes
    between job postings. Weights (see app.config.ATS_WEIGHTS):

      skill_match       40%  — share of the JD's skills present in the resume
      keyword_match     20%  — JD keywords present (synonym + fuzzy aware)
      semantic_match    15%  — embedding similarity (floor-calibrated)
      experience_match  15%  — years of experience vs. the role's requirement
      parseability      10%  — is the resume legible to a parser at all

    A category that cannot be evaluated (for example experience_match when the
    JD states no requirement) has its weight redistributed across the rest, so
    the score stays on a comparable 0-100 scale.

    Returns scores in the 0-100 range, each rounded to 2 decimals.
    """
    tfidf_score = tfidf_similarity(resume_text, jd_text)
    raw_semantic = semantic_similarity(resume_text, jd_text)
    used_semantic = raw_semantic is not None
    semantic_score = (
        _calibrate_semantic(raw_semantic) if used_semantic else tfidf_score
    )

    skill_score = skill_match_score(total_jd_skills, total_matched)
    keyword_score, keyword_detail = keyword_overlap_score(
        resume_text, jd_text, return_detail=True
    )
    parseability, parseability_detail = parseability_score(resume_text)

    # --- Individual category scores (all 0-100, None = not applicable) ---
    categories: dict[str, float | None] = {
        "skill_match": skill_score,
        "keyword_match": keyword_score,
        "semantic_match": semantic_score,
        "experience_match": experience_score,
        "parseability": parseability,
    }

    # --- Weighted final score over applicable categories only ---
    applicable = {k: v for k, v in categories.items() if v is not None and k in ATS_WEIGHTS}
    weight_total = sum(ATS_WEIGHTS[k] for k in applicable)
    final_score = (
        sum(ATS_WEIGHTS[k] * v for k, v in applicable.items()) / weight_total
        if weight_total > 0
        else 0.0
    )
    final_score = round(max(0.0, min(100.0, final_score)), 2)

    return {
        "semantic_score": semantic_score,
        "raw_semantic_score": raw_semantic,
        "tfidf_score": tfidf_score,
        "skill_score": skill_score,
        "keyword_score": keyword_score,
        "experience_score": experience_score,
        "parseability_score": parseability,
        "final_score": final_score,
        "used_semantic_model": used_semantic,
        "categories": {
            cat: (None if score is None else round(score, 2))
            for cat, score in categories.items()
        },
        "weights": dict(ATS_WEIGHTS),
        "keyword_detail": keyword_detail,
        "parseability_detail": parseability_detail,
    }


def parseability_score(resume_text: str) -> tuple[float, dict]:
    """
    0-100: can an ATS parser read this resume at all?

    This is the one resume-only signal that belongs in an ATS score. It is
    not about how good the candidate is -- it is about whether a parser can
    extract the requirements, so a resume scored on a wall of icons or a
    table layout is invisible regardless of content.

    Sub-signals and weights live in app.config.PARSEABILITY_WEIGHTS.
    """
    contact = _contact_score(resume_text)
    sections = _section_score(resume_text)
    formatting, _ = _formatting_risk_score(resume_text)
    length, _ = _length_structure_score(resume_text)

    parts = {
        "contact_info": contact,
        "section_structure": sections,
        "formatting": formatting,
        "length": length,
    }
    total_weight = sum(PARSEABILITY_WEIGHTS.get(k, 0.0) for k in parts)
    if total_weight <= 0:
        return 0.0, parts

    score = sum(PARSEABILITY_WEIGHTS[k] * v for k, v in parts.items()) / total_weight
    return round(max(0.0, min(100.0, score)), 2), parts


def _contact_score(resume_text: str) -> float:
    """
    0-100: fraction of key contact fields detected.

    A bare "LinkedIn" or "GitHub" mention counts. Requiring the full URL made
    this score disagree with the entity extractor's verdict on the very same
    resume, which is how the two score panels ended up contradicting each
    other.
    """
    checks = {
        "email": bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text)),
        "phone": bool(re.search(r"[\+]?[(]?\d{1,4}[)]?[-\s./]?\d{1,4}[-\s./]?\d{1,9}", resume_text)),
        "linkedin": bool(re.search(r"\blinkedin\b", resume_text, re.IGNORECASE)),
        "github": bool(re.search(r"\bgithub\b", resume_text, re.IGNORECASE)),
    }
    return round((sum(checks.values()) / len(checks)) * 100, 2)


def _section_score(resume_text: str) -> float:
    """0-100: fraction of core resume sections detected."""
    lower = resume_text.lower()
    core_sections = ["experience", "education", "skills", "projects"]
    found = sum(
        1 for s in core_sections
        if re.search(rf"\b{re.escape(s)}\b", lower)
    )
    return round((found / len(core_sections)) * 100, 2)

