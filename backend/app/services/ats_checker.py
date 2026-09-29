"""
ats_checker.py

Resume parseability signals and quality checks.

This module owns the resume-only signals that decide whether an ATS can read
a file: contact completeness, section structure, formatting risk and length,
plus the boolean quality checklist shown in the report.

The overall ATS score itself lives in app.services.similarity_service, which
is the single scoring engine. This module deliberately does NOT compute a
second, competing score: the previous design had one here and one there,
measured the same signals with different regexes, and the two panels
disagreed with each other on the same resume (e.g. contact 50% vs 100%,
achievements 33% vs 100%). One engine, one number.
"""
import re

ACTION_VERBS = {
    "achieved", "built", "created", "designed", "developed", "engineered",
    "established", "executed", "implemented", "improved", "increased",
    "initiated", "launched", "led", "managed", "optimized", "organized",
    "reduced", "researched", "resolved", "spearheaded", "streamlined",
    "supervised", "trained", "transformed", "delivered", "automated",
    "architected", "analyzed", "collaborated", "coordinated", "deployed",
    "mentored", "negotiated", "pioneered", "prototyped", "refactored",
    "configured", "integrated", "secured", "audited", "investigated",
    "diagnosed", "migrated", "standardized", "accelerated", "generated",
}

PERSONAL_PRONOUNS = {"i", "me", "my", "mine", "myself"}

STANDARD_SECTIONS = [
    "education", "experience", "work experience", "skills", "projects",
    "certifications", "summary", "objective", "achievements", "publications",
]


def _keyword_match_score(resume_text: str, jd_text: str) -> tuple[float, str]:
    """DEPRECATED: keyword scoring is owned by similarity_service now.

    Kept only as a compatibility shim for anything that imports it. The real
    keyword signal is IDF-weighted and synonym/fuzzy aware; this version was
    a bare TF-IDF top-25 word split that disagreed with it.
    """
    from app.services.similarity_service import keyword_overlap_score

    if not jd_text or not jd_text.strip():
        return 0.0, "No job description provided for keyword comparison."

    score = keyword_overlap_score(resume_text, jd_text)
    return score, f"Weighted job-description keyword coverage: {score}%."


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


def check_compatibility_indicators(resume_text: str, entities: dict, file_ext: str) -> dict:
    """
    Boolean pass/fail indicators only. The score lives in the unified
    similarity_service model, so this must never return a second number that
    can disagree with it.
    """
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

    return {"indicators": indicators}
