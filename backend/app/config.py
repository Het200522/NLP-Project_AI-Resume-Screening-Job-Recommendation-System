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
# Modeled after how real ATS systems (Workday, Taleo, Greenhouse, iCIMS)
# are publicly known to rank candidates.
ATS_WEIGHTS = {
    "keyword_match":     float(os.getenv("ATS_KEYWORD_WEIGHT",     "0.30")),
    "skill_match":       float(os.getenv("ATS_SKILL_WEIGHT",       "0.25")),
    "semantic_match":    float(os.getenv("ATS_SEMANTIC_WEIGHT",    "0.15")),
    "contact_info":      float(os.getenv("ATS_CONTACT_WEIGHT",     "0.10")),
    "section_structure": float(os.getenv("ATS_SECTION_WEIGHT",     "0.10")),
    "achievements":      float(os.getenv("ATS_ACHIEVEMENT_WEIGHT", "0.05")),
    "action_verbs":      float(os.getenv("ATS_VERB_WEIGHT",        "0.05")),
}

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
