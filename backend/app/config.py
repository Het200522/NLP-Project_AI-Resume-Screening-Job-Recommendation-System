"""
Central configuration for the AI Resume Screener backend.
All tunable parameters (scoring weights, model names, limits) live here
so they don't get scattered across services.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'resume_screener.db'}")

# --- CORS ---
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# --- File upload limits ---
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_JD_EXTENSIONS = {".txt", ".pdf", ".docx"}

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"

# --- NLP / ML ---
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")

# Whether to attempt loading the sentence-transformer model at all.
# On constrained environments (no internet at runtime, low RAM) this can be
# disabled and the system will gracefully fall back to TF-IDF-only scoring.
ENABLE_SEMANTIC_MODEL = os.getenv("ENABLE_SEMANTIC_MODEL", "true").lower() == "true"

# --- Real-world ATS scoring weights (must sum to 1.0) ---
#
# One unified score. Proprietary ATS algorithms are undisclosed, but their
# behaviour is publicly documented: they rank on how much of the job's
# requirements a resume covers, and only treat resume hygiene as a
# prerequisite for the text being readable at all.
#
# Consequence of that model: requirement coverage carries 90% of the weight
# and parseability carries 10%. The previous split spent 70% of the
# "ATS readiness" score on hygiene (sections, contact, achievements, verbs,
# formatting, length) and only 30% on the job, which meant a resume with
# zero skill overlap but tidy formatting still scored ~70 -- and it made the
# two score panels disagree with each other on the same resume.
#
# Hard minimums the JD states outright (years, degree, named certifications)
# are NOT scored here. They are evaluated as knockout gates and reported
# separately, the way an ATS filters before ranking.
ATS_WEIGHTS = {
    "skill_match":      float(os.getenv("ATS_SKILL_WEIGHT",      "0.40")),
    "keyword_match":    float(os.getenv("ATS_KEYWORD_WEIGHT",    "0.20")),
    "semantic_match":   float(os.getenv("ATS_SEMANTIC_WEIGHT",   "0.15")),
    "experience_match": float(os.getenv("ATS_EXPERIENCE_WEIGHT", "0.15")),
    "parseability":     float(os.getenv("ATS_PARSEABILITY_WEIGHT", "0.10")),
}

# Sub-weights inside the single parseability category. These are the signals
# that decide whether an ATS can read the resume at all.
PARSEABILITY_WEIGHTS = {
    "contact_info":      float(os.getenv("ATSP_CONTACT_WEIGHT",      "0.30")),
    "section_structure": float(os.getenv("ATSP_SECTION_WEIGHT",      "0.25")),
    "formatting":        float(os.getenv("ATSP_FORMATTING_WEIGHT",    "0.25")),
    "length":            float(os.getenv("ATSP_LENGTH_WEIGHT",        "0.20")),
}

# Sentence embeddings place two unrelated professional documents at a cosine
# similarity of roughly 0.35-0.50, so an uncalibrated semantic score hands
# ~45/100 to a completely mismatched candidate. Everything at or below this
# floor is rescaled to 0.
SEMANTIC_FLOOR = float(os.getenv("SEMANTIC_FLOOR", "40"))

# The matching end of the band. Cosine similarity for two genuinely aligned
# resume/JD pairs rarely exceeds ~0.75 with this model, so treating 100 as
# reachable would compress every realistic match into the bottom third of the
# range. The usable band is rescaled from [FLOOR, CEILING] onto 0-100.
SEMANTIC_CEILING = float(os.getenv("SEMANTIC_CEILING", "75"))
assert SEMANTIC_CEILING > SEMANTIC_FLOOR, (
    f"SEMANTIC_CEILING ({SEMANTIC_CEILING}) must exceed "
    f"SEMANTIC_FLOOR ({SEMANTIC_FLOOR})"
)

_total = sum(ATS_WEIGHTS.values())
assert abs(_total - 1.0) < 1e-6, (
    f"ATS_WEIGHTS must sum to 1.0, got {_total}"
)

# --- Match score labels (for candidate ranking table) ---
def score_to_status(score: float) -> str:
    if score >= 85:
        return "Strong Match"
    if score >= 70:
        return "Good Match"
    if score >= 50:
        return "Partial Match"
    return "Low Match"
