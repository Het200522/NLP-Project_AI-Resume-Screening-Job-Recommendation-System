"""
Tests for hard minimum requirements (knockout gates).

These are the requirements a real ATS filters on before ranking anyone. The
important property is that they are reported as pass/fail, never folded into
the numeric score: a candidate who misses one is told what is missing instead
of being silently buried under a lower number.
"""
from app.services.knockout import evaluate_knockouts


def test_jd_with_no_hard_minimums_evaluates_nothing_and_passes():
    """A posting that states no minimums must not invent a failing gate."""
    result = evaluate_knockouts(
        "Python developer with five years of experience.",
        "We are looking for a Python developer to join our team and build things.",
    )
    assert result["evaluated"] is False
    assert result["gates"] == []
    assert result["failed"] == []
    assert result["passed"] is True


def test_minimum_experience_gate_fails_when_resume_is_short():
    result = evaluate_knockouts(
        "Recent graduate with a project portfolio.",
        "Senior Engineer. Requirements: 8+ years of backend engineering experience.",
    )
    assert result["evaluated"] is True
    assert result["passed"] is False
    assert "Minimum experience" in result["failed"]


def test_minimum_experience_gate_passes_when_resume_meets_it():
    resume = (
        "Software Engineer, Acme (2018-2025)\nEngineered backend services.\n"
        "Backend Engineer, Globex (2016-2018)\nBuilt REST APIs."
    )
    result = evaluate_knockouts(resume, "Engineer. Requirements: 5+ years of experience.")
    assert result["passed"] is True
    assert result["failed"] == []


def test_degree_gate_only_triggers_on_a_stated_requirement():
    """A passing mention of a degree is not a gate; 'degree required' is."""
    mention_only = evaluate_knockouts(
        "Engineer with a bachelor's degree.",
        "Our team enjoys collaborating. Bachelor's degree holders do great here.",
    )
    assert mention_only["evaluated"] is False

    stated = evaluate_knockouts(
        "Engineer with a bachelor's degree.",
        "Bachelor's degree required. You will build payment services.",
    )
    assert stated["evaluated"] is True
    assert stated["passed"] is True


def test_degree_gate_fails_when_resume_lacks_the_level():
    result = evaluate_knockouts(
        "Engineer with a bachelor's degree and five years of experience.",
        "Lead Engineer. Master's degree required. You will lead a platform team.",
    )
    assert result["passed"] is False
    assert "Minimum education" in result["failed"]


def test_higher_degree_satisfies_a_lower_requirement():
    result = evaluate_knockouts(
        "Engineer with a Master's degree and six years of experience.",
        "Engineer. Bachelor's degree required. You will build services.",
    )
    assert result["passed"] is True


def test_named_certification_gate_is_detected_and_checked():
    resume_without = "Backend engineer with Python and Kubernetes experience."
    jd = "CKA certification required. Must have strong Python skills."

    result = evaluate_knockouts(resume_without, jd)
    assert result["passed"] is False
    assert "Required certification" in result["failed"]
    certs = " ".join(g["requirement"] for g in result["gates"])
    assert "CKA" in certs


def test_certification_present_on_resume_satisfies_the_gate():
    resume_with = "Backend engineer, CKA certified, with Python and Kubernetes experience."
    jd = "CKA certification required. Must have strong Python skills."

    result = evaluate_knockouts(resume_with, jd)
    assert result["passed"] is True


def test_knockouts_do_not_change_the_numeric_score():
    """
    The score and the gates are independent: the same resume scores the same
    whether or not the posting states a minimum. Otherwise a gate failure would
    be double-counted and the reason would be invisible.
    """
    resume = "Recent graduate with a portfolio and one internship."
    jd_without = "Python developer to build services with FastAPI and PostgreSQL."
    jd_with = (
        "Senior Python developer. Requirements: 12+ years of experience. "
        "PhD required. CISSP certification required."
    )

    from app.services.similarity_service import compute_final_score

    kwargs = dict(total_jd_skills=4, total_matched=2, experience_score=40.0)
    a = compute_final_score(resume, jd_without, **kwargs)
    b = compute_final_score(resume, jd_with, **kwargs)

    assert evaluate_knockouts(resume, jd_with)["passed"] is False
    # Only the keyword text differs, so the point here is that the gate verdict
    # lives outside the score payload entirely.
    assert set(a["categories"]) == set(b["categories"])
    assert "knockout" not in a and "knockout" not in b
