from app.services.skill_extractor import extract_skills, diff_skills


def test_extract_skills_finds_known_skills(sample_resume_text):
    skills = extract_skills(sample_resume_text)
    names = {s["skill"] for s in skills}
    assert "Python" in names
    assert "FastAPI" in names
    assert "Docker" in names
    assert "PostgreSQL" in names


def test_extract_skills_avoids_false_positive_substring():
    # "R" should not match inside "Learning" or other words containing 'r'.
    text = "We use Java and JavaScript for scripting purposes."
    skills = extract_skills(text)
    names = {s["skill"] for s in skills}
    assert "R" not in names
    assert "Java" in names
    assert "JavaScript" in names


def test_extract_skills_empty_text_returns_empty_list():
    assert extract_skills("") == []


def test_short_language_tokens_require_domain_context():
    """'Go', 'C' and 'R' are ambiguous English words, so they need context."""
    assert extract_skills("I go to college and study hard.") == []
    assert extract_skills("Grade C in mathematics, section R of the handbook.") == []

    names = {s["skill"] for s in extract_skills("Go microservices with gRPC on Kubernetes.")}
    assert "Go" in names

    names = {s["skill"] for s in extract_skills("Statistical modelling in R with ggplot.")}
    assert "R" in names

    names = {s["skill"] for s in extract_skills("Programming in C using pointers.")}
    assert "C" in names


def test_security_domain_skills_are_recognised():
    text = (
        "Operate Splunk and QRadar SIEM platforms. Configure firewalls, IDS/IPS "
        "and SOAR playbooks. Run OWASP Top 10 penetration testing, handle incident "
        "response, and perform threat modeling with STRIDE."
    )
    names = {s["skill"] for s in extract_skills(text)}
    for expected in [
        "SIEM", "Splunk", "QRadar", "Firewall", "IDS/IPS", "SOAR", "OWASP",
        "Penetration Testing", "Incident Response", "Threat Modeling",
    ]:
        assert expected in names, f"{expected} not extracted"


def test_diff_skills_matched_missing_additional():
    resume_skills = [{"skill": "Python", "category": "Programming"}, {"skill": "Docker", "category": "Cloud/DevOps"}]
    jd_skills = [{"skill": "Python", "category": "Programming"}, {"skill": "AWS", "category": "Cloud/DevOps"}]

    diff = diff_skills(resume_skills, jd_skills)
    assert diff["matched_skills"] == ["Python"]
    assert diff["missing_skills"] == ["AWS"]
    assert diff["additional_skills"] == ["Docker"]
    assert diff["total_jd_skills"] == 2


def test_diff_skills_reports_required_and_preferred_tiers():
    resume = [{"skill": "Python", "category": "Programming"}]
    required = [{"skill": "Python"}, {"skill": "Splunk"}]
    preferred = [{"skill": "AWS"}]

    diff = diff_skills(resume, required + preferred, required, preferred)

    assert diff["total_required"] == 2
    assert diff["total_matched_required"] == 1
    assert diff["total_preferred"] == 1
    assert diff["total_matched_preferred"] == 0
    assert diff["matched_required"] == ["Python"]
    assert diff["missing_required"] == ["Splunk"]
    assert diff["missing_preferred"] == ["AWS"]
