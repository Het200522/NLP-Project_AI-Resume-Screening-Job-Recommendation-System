"""
Regression tests for the original defect: an AI/ML student scored the same
against a Cybersecurity Analyst role as against roles that actually fit,
because the role's skills were never extracted and 30% of the score was
identical for every role.
"""
from app.services.skill_extractor import extract_skills, diff_skills
from app.services.jd_parser import parse_job_description
from app.services.similarity_service import compute_final_score
from app.services.experience_service import (
    estimate_years_of_experience,
    experience_match_score,
    parse_experience_requirement,
)
from app.services.role_templates import ROLES


AIML_STUDENT = """
Aarav Sharma
aarav.sharma@example.com | +91 98765 43210 | linkedin.com/in/aaravsharma | github.com/aaravsharma

EDUCATION
B.Tech in Computer Science (AI & ML), Vellore Institute of Technology, 2022-2026, CGPA 8.7

SKILLS
Python, Java, Machine Learning, Deep Learning, NLP, TensorFlow, PyTorch, Pandas, NumPy,
Scikit-learn, OpenCV, Computer Vision, SQL, MongoDB, Git, Docker, REST API, Linux, Tableau

PROJECTS
- Built a chatbot using NLP and Transformer models that classifies student intents with 92% accuracy.
- Developed an image classification model with CNN architectures and OpenCV, achieving 88% validation accuracy.

EXPERIENCE
Data Science Intern, Tech Startup (2024)
- Analyzed customer data using Pandas and visualized results with Tableau and Matplotlib.
"""


def _score(resume: str, role_id: str) -> dict:
    jd = ROLES[role_id]["description"]
    info = parse_job_description(jd)
    diff = diff_skills(
        extract_skills(resume), info["all_skills"],
        info["required_skills"], info["preferred_skills"],
    )
    exp = estimate_years_of_experience(resume)
    return compute_final_score(
        resume, jd,
        total_jd_skills=diff["total_jd_skills"], total_matched=diff["total_matched"],
        experience_score=experience_match_score(
            exp["years"], parse_experience_requirement(jd)
        ),
    )


def test_cybersecurity_role_actually_extracts_its_skills():
    """
    Regression: the role yielded only AWS, Azure and Python (3 skills, all
    optional or generic) because the skill taxonomy had no Security domain.
    """
    info = parse_job_description(ROLES["cybersecurity_analyst"]["description"])
    required = {s["skill"] for s in info["required_skills"]}

    assert len(required) >= 10
    for expected in ["SIEM", "OWASP", "Firewall", "Incident Response", "IDS/IPS"]:
        assert expected in required, f"{expected} missing from required skills"


def test_cybersecurity_gap_is_reported_to_an_aiml_student():
    info = parse_job_description(ROLES["cybersecurity_analyst"]["description"])
    diff = diff_skills(
        extract_skills(AIML_STUDENT), info["all_skills"],
        info["required_skills"], info["preferred_skills"],
    )

    # The student shares only Python with the core security requirements.
    assert set(diff["matched_required"]) <= {"Python"}
    for expected in ["SIEM", "OWASP", "Penetration Testing", "Firewall"]:
        assert expected in diff["missing_required"]


def test_student_ranks_matching_roles_above_unrelated_roles():
    """
    Regression: every role landed in a 37-54 band, so an AIML student looked
    equally plausible for Cybersecurity Analyst and for Data Scientist.
    """
    fitting = _score(AIML_STUDENT, "data_scientist")["final_score"]
    ml_role = _score(AIML_STUDENT, "ml_engineer")["final_score"]
    security = _score(AIML_STUDENT, "cybersecurity_analyst")["final_score"]
    design = _score(AIML_STUDENT, "ux_designer")["final_score"]

    assert fitting > security
    assert ml_role > security
    assert security > design
    # The unrelated role must be decisively excluded, not merely ranked lower.
    assert security < 30
    assert design < 20


def test_scores_spread_meaningfully_across_roles():
    scores = {rid: _score(AIML_STUDENT, rid)["final_score"] for rid in ROLES}
    spread = max(scores.values()) - min(scores.values())
    assert spread > 25, f"scores still compressed into a {spread:.1f} point band: {scores}"


def test_every_role_produces_usable_skill_requirements():
    """No role may be reduced to a handful of generic skills."""
    for role_id in ROLES:
        info = parse_job_description(ROLES[role_id]["description"])
        assert len(info["required_skills"]) >= 6, (
            f"{role_id} extracted only {len(info['required_skills'])} required skills"
        )
        assert info["all_skills"], f"{role_id} produced no skills at all"


ENTRY_LEVEL_ROLES = [
    "entry_ml_engineer", "junior_data_scientist",
    "junior_software_engineer", "junior_backend_engineer",
]


def test_entry_level_roles_exist_and_are_actually_entry_level():
    """
    Every original template required 2-8 years, so a fresher failed the
    experience gate on all 13 and lost the same 15 points everywhere. The
    score could not tell a fresher-appropriate role from a senior one.
    """
    for role_id in ENTRY_LEVEL_ROLES:
        assert role_id in ROLES, f"{role_id} missing from role templates"
        req = parse_experience_requirement(ROLES[role_id]["description"])
        assert req is not None, f"{role_id} states no experience requirement"
        # min 0.0 means the gate does not fire and 0 years scores full marks.
        assert req.min_years == 0.0, (
            f"{role_id} requires {req.min_years}+ years, which is not entry level"
        )
        assert experience_match_score(0.0, req) == 100.0


def test_fresher_passes_entry_level_gates_and_fails_senior_gates():
    from app.services.knockout import evaluate_knockouts

    fresher = AIML_STUDENT

    for role_id in ENTRY_LEVEL_ROLES:
        result = evaluate_knockouts(fresher, ROLES[role_id]["description"])
        exp_gates = [g for g in result["gates"] if g["label"] == "Minimum experience"]
        assert not exp_gates, (
            f"{role_id} raised an experience gate despite being entry level"
        )

    # The same resume must still hit the hard requirement on a senior template.
    senior = evaluate_knockouts(fresher, ROLES["backend_engineer"]["description"])
    assert senior["passed"] is False
    assert "Minimum experience" in senior["failed"]


def test_student_scores_higher_on_entry_level_roles_than_their_senior_equivalents():
    """
    Same resume, same discipline: an entry-level posting must score clearly
    above the 3-6 year posting, because the experience category and the
    seniority-flavoured skill sets both favour it.
    """
    pairs = [
        ("entry_ml_engineer", "ml_engineer"),
        ("junior_data_scientist", "data_scientist"),
        ("junior_backend_engineer", "backend_engineer"),
    ]
    for junior_id, senior_id in pairs:
        junior = _score(AIML_STUDENT, junior_id)["final_score"]
        senior = _score(AIML_STUDENT, senior_id)["final_score"]
        assert junior > senior, (
            f"{junior_id} ({junior}) should out-score {senior_id} ({senior})"
        )
        assert junior - senior >= 5, (
            f"{junior_id} only {junior - senior:.1f} above {senior_id}; "
            "the entry-level signal is too weak to be meaningful"
        )
