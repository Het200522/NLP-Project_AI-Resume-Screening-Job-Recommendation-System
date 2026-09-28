"""
ats_checker.py

A comprehensive, weighted "Resume Compatibility / ATS Readiness Score"
built from the same signal categories real-world ATS and resume-parsing
tools are publicly known to weigh: keyword match, section structure,
contact completeness, quantifiable achievements, action-verb usage,
formatting risk, and length.

This is NOT a reproduction of any proprietary vendor's (Workday, Taleo,
Greenhouse, iCIMS, etc.) internal algorithm -- those are undisclosed and
cannot be legitimately replicated. It is a transparent, rule-based model
built on widely published ATS best practices, and every sub-score is
explainable and traceable to a concrete signal in the resume text.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.preprocess import preprocess_for_matching

ACTION_VERBS = {
    "achieved", "built", "created", "designed", "developed", "engineered",
    "established", "executed", "implemented", "improved", "increased",
    "initiated", "launched", "led", "managed", "optimized", "organized",
    "reduced", "researched", "resolved", "spearheaded", "streamlined",
    "supervised", "trained", "transformed", "delivered", "automated",
    "architected", "analyzed", "collaborated", "coordinated", "deployed",
    "mentored", "negotiated", "pioneered", "prototyped", "refactored",
}

PERSONAL_PRONOUNS = {"i", "me", "my", "mine", "myself"}

STANDARD_SECTIONS = [
    "education", "experience", "work experience", "skills", "projects",
    "certifications", "summary", "objective", "achievements", "publications",
]

# Category weights must sum to 1.0
WEIGHTS = {
    "keyword_match": 0.30,
    "section_structure": 0.15,
    "contact_completeness": 0.10,
    "quantifiable_achievements": 0.15,
    "action_verb_usage": 0.10,
    "formatting_risk": 0.10,
    "length_structure": 0.10,
}


def _keyword_match_score(resume_text: str, jd_text: str) -> tuple[float, str]:
    """Fraction of the JD's top TF-IDF keywords that appear in the resume."""
    if not jd_text or not jd_text.strip():
        return 0.0, "No job description provided for keyword comparison."

    jd_clean = preprocess_for_matching(jd_text)
    resume_clean = preprocess_for_matching(resume_text)
    if not jd_clean.strip():
        return 0.0, "Job description produced no usable keywords."

    vectorizer = TfidfVectorizer(max_features=25)
    try:
        vectorizer.fit([jd_clean])
    except ValueError:
        return 0.0, "Could not extract keywords from job description."

    jd_keywords = set(vectorizer.get_feature_names_out())
    resume_tokens = set(resume_clean.split())
    overlap = jd_keywords & resume_tokens

    if not jd_keywords:
        return 0.0, "No job description keywords found."

    score = (len(overlap) / len(jd_keywords)) * 100
    detail = f"{len(overlap)} of {len(jd_keywords)} top job-description keywords found in resume."
    return round(score, 1), detail


def _section_structure_score(resume_text: str) -> tuple[float, str, list[str]]:
    found = []
    lower = resume_text.lower()
    for section in STANDARD_SECTIONS:
        pattern = rf"^\s*{re.escape(section)}\s*:?\s*$"
        if re.search(pattern, lower, re.MULTILINE) or re.search(rf"\b{re.escape(section)}\b", lower):
            found.append(section)

    unique_core = {s for s in found if s in ("education", "experience", "work experience", "skills", "projects")}
    score = min(100.0, (len(unique_core) / 4) * 100)
    detail = f"Detected section headings: {', '.join(sorted(set(found))) or 'none'}."
    return round(score, 1), detail, found


def _contact_completeness_score(entities: dict) -> tuple[float, str]:
    fields = ["email", "phone", "name", "linkedin", "github"]
    present = [f for f in fields if entities.get(f)]
    score = (len(present) / len(fields)) * 100
    missing = [f for f in fields if not entities.get(f)]
    detail = f"Missing: {', '.join(missing)}." if missing else "All key contact fields detected."
    return round(score, 1), detail


def _quantifiable_achievements_score(resume_text: str) -> tuple[float, str]:
    matches = re.findall(r"(\$\s?\d[\d,]*|\d+(\.\d+)?\s?%|\b\d+x\b|\b\d{2,}\+?\b)", resume_text)
    count = len(matches)
    score = min(100.0, (count / 5) * 100)
    detail = f"Found {count} quantified achievement indicator(s) (numbers, %, $, etc.)."
    return round(score, 1), detail


def _action_verb_score(resume_text: str) -> tuple[float, str]:
    line_starts = []
    for line in resume_text.splitlines():
        stripped = line.strip().lstrip("-•●▪◦‣*").strip()
        if not stripped:
            continue
        words = stripped.split()
        if words:
            line_starts.append(words[0].lower().strip(".,:;"))
    verb_starts = sum(1 for w in line_starts if w in ACTION_VERBS)
    total_lines = max(1, len(line_starts))
    ratio = verb_starts / total_lines
    score = min(100.0, ratio * 300)
    detail = f"{verb_starts} line(s) start with a strong action verb out of {total_lines} content line(s)."
    return round(score, 1), detail


def _formatting_risk_score(resume_text: str) -> tuple[float, str]:
    penalties = []
    score = 100.0

    tab_heavy = resume_text.count("\t") > 20
    if tab_heavy:
        score -= 25
        penalties.append("heavy tab/column usage (may indicate a table-based layout)")

    special_char_ratio = len(re.findall(r"[^\w\s.,;:()\-/@%$]", resume_text)) / max(1, len(resume_text))
    if special_char_ratio > 0.03:
        score -= 20
        penalties.append("high density of unusual symbols/icons")

    pronoun_count = sum(
        1 for w in re.findall(r"[A-Za-z]+", resume_text.lower()) if w in PERSONAL_PRONOUNS
    )
    if pronoun_count > 5:
        score -= 10
        penalties.append("frequent first-person pronouns (less common in ATS-optimized resumes)")

    score = max(0.0, score)
    detail = "No major formatting risks detected." if not penalties else "Risks: " + "; ".join(penalties) + "."
    return round(score, 1), detail


def _length_structure_score(resume_text: str) -> tuple[float, str]:
    word_count = len(resume_text.split())
    if word_count < 150:
        score = max(0.0, (word_count / 150) * 60)
        detail = f"Resume is short ({word_count} words); may lack sufficient detail."
    elif word_count > 1200:
        score = max(0.0, 100 - ((word_count - 1200) / 20))
        detail = f"Resume is long ({word_count} words); consider tightening it."
    else:
        score = 100.0
        detail = f"Resume length ({word_count} words) is in a reasonable range."
    return round(max(0.0, min(100.0, score)), 1), detail


def compute_ats_score(resume_text: str, jd_text: str, entities: dict) -> dict:
    keyword_score, keyword_detail = _keyword_match_score(resume_text, jd_text)
    section_score, section_detail, _ = _section_structure_score(resume_text)
    contact_score, contact_detail = _contact_completeness_score(entities)
    quant_score, quant_detail = _quantifiable_achievements_score(resume_text)
    verb_score, verb_detail = _action_verb_score(resume_text)
    format_score, format_detail = _formatting_risk_score(resume_text)
    length_score, length_detail = _length_structure_score(resume_text)

    categories = {
        "keyword_match": {"score": keyword_score, "weight": WEIGHTS["keyword_match"], "detail": keyword_detail},
        "section_structure": {"score": section_score, "weight": WEIGHTS["section_structure"], "detail": section_detail},
        "contact_completeness": {"score": contact_score, "weight": WEIGHTS["contact_completeness"], "detail": contact_detail},
        "quantifiable_achievements": {"score": quant_score, "weight": WEIGHTS["quantifiable_achievements"], "detail": quant_detail},
        "action_verb_usage": {"score": verb_score, "weight": WEIGHTS["action_verb_usage"], "detail": verb_detail},
        "formatting_risk": {"score": format_score, "weight": WEIGHTS["formatting_risk"], "detail": format_detail},
        "length_structure": {"score": length_score, "weight": WEIGHTS["length_structure"], "detail": length_detail},
    }

    overall = sum(c["score"] * c["weight"] for c in categories.values())
    overall = round(max(0.0, min(100.0, overall)), 1)

    if overall >= 85:
        band = "Excellent ATS readiness"
    elif overall >= 70:
        band = "Good ATS readiness"
    elif overall >= 50:
        band = "Needs improvement"
    else:
        band = "High risk of being filtered out"

    recommendations = [
        f"Improve {name.replace('_', ' ')}: {c['detail']}"
        for name, c in categories.items() if c["score"] < 60
    ]

    return {
        "overall_score": overall,
        "band": band,
        "categories": categories,
        "recommendations": recommendations,
        "disclaimer": (
            "This is an independent, rule-based ATS readiness estimate based on "
            "publicly documented resume-parsing best practices. It does not "
            "reproduce any specific ATS vendor's proprietary scoring algorithm "
            "and is not a guarantee of how any real system will score this resume."
        ),
    }


def check_resume_quality(resume_text: str, entities: dict, skills: list[dict]) -> dict:
    checks = []

    def add(label: str, passed: bool, detail: str = ""):
        checks.append({"label": label, "passed": passed, "detail": detail})

    word_count = len(resume_text.split())

    add("Contact information detected", bool(entities.get("email") and entities.get("phone")))
    add("Email detected", bool(entities.get("email")))
    add("Phone number detected", bool(entities.get("phone")))
    add("Skills section detected", len(skills) > 0)
    add("GitHub profile detected", bool(entities.get("github")))
    add("LinkedIn profile detected", bool(entities.get("linkedin")))
    add("Education section detected", bool(re.search(r"\b(education|degree|university|college|bachelor|master|b\.?tech|m\.?tech)\b", resume_text, re.IGNORECASE)))
    add("Experience section detected", bool(re.search(r"\b(experience|internship|worked at|employment)\b", resume_text, re.IGNORECASE)))
    add("Projects section detected", bool(re.search(r"\b(projects?|portfolio)\b", resume_text, re.IGNORECASE)))
    add("Resume length reasonable (150-1200 words)", 150 <= word_count <= 1200, f"Resume has {word_count} words.")
    add("Text extractable (not an image-only PDF)", word_count > 20)

    passed_count = sum(1 for c in checks if c["passed"])
    return {
        "checks": checks,
        "passed": passed_count,
        "total": len(checks),
        "score_percent": round((passed_count / len(checks)) * 100, 1) if checks else 0.0,
    }


def check_compatibility_indicators(resume_text: str, jd_text: str, entities: dict, file_ext: str) -> dict:
    indicators = []

    def add(label: str, ok: bool, note: str = ""):
        indicators.append({"label": label, "ok": ok, "note": note})

    add("Standard file format", file_ext.lower() in (".pdf", ".docx"), f"File type: {file_ext}")
    add("Text is extractable", len(resume_text.strip()) > 50,
        "Little or no text could be extracted; the file may be a scanned image.")

    section_headers = re.findall(
        r"^\s*(education|experience|skills|projects|certifications|summary|objective)\s*$",
        resume_text, re.IGNORECASE | re.MULTILINE,
    )
    add("Standard section headings found", len(section_headers) >= 2,
        f"Found {len(section_headers)} recognizable section heading(s).")

    table_hint = resume_text.count("\t") > 20
    add("Low reliance on complex tables", not table_hint,
        "Heavy tab-separated content detected; tables can confuse some parsers." if table_hint else "")

    word_count = len(resume_text.split())
    add("Reasonable resume length", 150 <= word_count <= 1200, f"{word_count} words detected.")

    ats = compute_ats_score(resume_text, jd_text, entities)

    return {"indicators": indicators, "ats_score": ats}
