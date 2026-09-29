"""
knockout.py
Hard minimum requirements ("knockout questions").

Real ATS platforms ask minimum-qualification questions *before* ranking a
candidate. A posting that says "5+ years of Kubernetes experience" or
"Masters degree required" is not a preference to be averaged into a score --
it is a filter. Greenhouse and Lever expose these as explicit gate questions,
and a candidate who fails one is either not surfaced at all or ranked last
regardless of how strong the rest of the profile is.

This module separates that behaviour from the score: it reports which gates
the job states, whether the resume meets them, and what the failure is. The
gate verdict deliberately does NOT reduce the numeric score, so a candidate
is not silently buried -- they are told exactly what is missing.
"""
import re

from app.services.experience_service import (
    estimate_years_of_experience,
    parse_experience_requirement,
)

# Degree levels, ordered. A posting that names a level is asking for at least
# that level.
_DEGREE_LEVELS: list[tuple[str, int]] = [
    ("phd", 4), ("doctorate", 4),
    ("master", 3), ("m.tech", 3), ("mtech", 3), ("m.s.", 3), ("msc", 3),
    ("m.sc", 3), ("mca", 3), ("mba", 3), ("m.a.", 3), ("meng", 3),
    ("bachelor", 2), ("b.tech", 2), ("btech", 2), ("b.s.", 2), ("bsc", 2),
    ("b.sc", 2), ("b.e.", 2), ("bca", 2), ("bba", 2), ("b.a.", 2), ("beng", 2),
    ("associate", 1), ("diploma", 1),
    ("high school", 1), ("highschool", 1), ("secondary", 1), ("h.s.c", 1),
]

# Phrases that mark a requirement as a hard minimum rather than a preference.
_HARD_REQUIREMENT = re.compile(
    r"\b(?:required|requirement|must\s+(?:have|be|hold|possess|include)|"
    r"essential|mandatory|minimum|at\s+least|strongly\s+(?:preferred|required)|"
    r"only\s+consider|no\s+substitute)\b",
    re.IGNORECASE,
)

# A certification named in a hard-requirement context.
_CERT_CONTEXT = re.compile(
    r"(?:certification|certificate|certified|accreditation|licen[cs]e)\b[^.\n]{0,60}",
    re.IGNORECASE,
)
_CERT_NAMES = re.compile(
    r"\b(?:AWS Certified [A-Za-z ]+?|Azure [A-Z][A-Za-z ]+?|Google Cloud [A-Za-z ]+?|"
    r"CKA|CKAD|PMP|CAPM|CISSP|CISM|CISA|CCNA|CCNP|CCIE|Security\+|"
    r"CompTIA [A-Za-z+]+|ITIL|TFCS|TensorFlow Developer|Certified Scrum Master|"
    r"Six Sigma(?: Black Belt)?|PMP|CFRN|CPCE|ACCA|CPA|CMA)\b",
    re.IGNORECASE,
)


def _has_hard_context(text: str) -> bool:
    return bool(_HARD_REQUIREMENT.search(text))


def _detect_degree(text: str) -> tuple[str, int] | None:
    """
    Returns the highest degree level mentioned, as (label, rank). A resume
    listing both a B.Tech and a Masters is treated as the higher level, which
    is what a recruiter reads it as.
    """
    lowered = text.lower()
    best: tuple[str, int] | None = None
    for label, rank in _DEGREE_LEVELS:
        if re.search(r"(?<![a-z])" + re.escape(label) + r"(?![a-z])", lowered):
            if best is None or rank > best[1]:
                best = (label, rank)
    return best


def _required_degree_from_jd(jd_text: str) -> tuple[str, int] | None:
    """
    Only treats a degree as a gate when the posting states it as a minimum.
    "Bachelor's degree required" is a gate; a passing mention of a degree is
    not.
    """
    for sentence in re.split(r"[.\n]", jd_text):
        if not _has_hard_context(sentence):
            continue
        found = _detect_degree(sentence)
        if found:
            return found
    return None


def _required_certifications(jd_text: str) -> list[str]:
    """Named certifications that appear in a hard-requirement context."""
    certs: list[str] = []
    for sentence in re.split(r"[.\n]", jd_text):
        if not _has_hard_context(sentence):
            continue
        for m in _CERT_NAMES.finditer(sentence):
            name = m.group(0).strip()
            if name.lower() not in {c.lower() for c in certs}:
                certs.append(name)
    # "Certification required" with no named cert is still a gate.
    if not certs and _has_hard_context(jd_text) and _CERT_CONTEXT.search(jd_text):
        certs.append("a relevant professional certification")
    return certs


def evaluate_knockouts(
    resume_text: str,
    jd_text: str,
    resume_experience: dict | None = None,
) -> dict:
    """
    Evaluates the hard minimums the job description states.

    Returns a dict with:
      gates: list of {label, requirement, requirement_met, detail}
      failed: list of labels the resume does not meet
      passed: bool -- False when the JD states a gate the resume fails
      evaluated: bool -- False when the JD states no hard minimums at all

    A gate the job never states is reported as met, so `passed` is only False
    for a real, stated requirement. Nothing here changes the numeric score.
    """
    if resume_experience is None:
        resume_experience = estimate_years_of_experience(resume_text)

    gates: list[dict] = []

    # --- Gate 1: minimum years of experience ---
    requirement = parse_experience_requirement(jd_text)
    years = resume_experience.get("years", 0.0)
    if requirement and requirement.min_years:
        met = years >= requirement.min_years
        gates.append({
            "label": "Minimum experience",
            "requirement": requirement.raw or f"{requirement.min_years}+ years",
            "requirement_met": met,
            "detail": (
                f"Role asks for {requirement.min_years}+ year(s); resume shows "
                f"{years} year(s)."
            ),
        })

    # --- Gate 2: minimum degree level ---
    required_degree = _required_degree_from_jd(jd_text)
    if required_degree:
        label, rank = required_degree
        resume_degree = _detect_degree(resume_text)
        met = resume_degree is not None and resume_degree[1] >= rank
        gates.append({
            "label": "Minimum education",
            "requirement": f"{label.upper()} or equivalent",
            "requirement_met": met,
            "detail": (
                f"Role requires at least {label}; resume shows "
                + (f"{resume_degree[0].upper()}" if resume_degree else "no degree detected")
            ),
        })

    # --- Gate 3: named certifications ---
    for cert in _required_certifications(jd_text):
        # A resume "holds" a certification if its name appears, or if the
        # resume mentions certification at all for the generic gate.
        met = bool(
            re.search(re.escape(cert), resume_text, re.IGNORECASE)
            or (
                cert.startswith("a relevant")
                and re.search(r"certificat|licen[cs]e|accredit", resume_text, re.IGNORECASE)
            )
        )
        gates.append({
            "label": "Required certification",
            "requirement": cert,
            "requirement_met": met,
            "detail": (
                f"{cert} is named as a requirement and "
                + ("appears on the resume." if met else "was not found on the resume.")
            ),
        })

    failed = [g["label"] for g in gates if not g["requirement_met"]]

    return {
        "gates": gates,
        "failed": failed,
        "passed": not failed,
        "evaluated": bool(gates),
    }
