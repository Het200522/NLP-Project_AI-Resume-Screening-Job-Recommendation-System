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
