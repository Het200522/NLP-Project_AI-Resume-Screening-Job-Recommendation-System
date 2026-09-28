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


def test_diff_skills_matched_missing_additional():
    resume_skills = [{"skill": "Python", "category": "Programming"}, {"skill": "Docker", "category": "Cloud/DevOps"}]
    jd_skills = [{"skill": "Python", "category": "Programming"}, {"skill": "AWS", "category": "Cloud/DevOps"}]

    diff = diff_skills(resume_skills, jd_skills)
    assert diff["matched_skills"] == ["Python"]
    assert diff["missing_skills"] == ["AWS"]
    assert diff["additional_skills"] == ["Docker"]
    assert diff["total_jd_skills"] == 2
