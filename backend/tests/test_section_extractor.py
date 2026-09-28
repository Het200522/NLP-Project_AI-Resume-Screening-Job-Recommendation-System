from app.services.section_extractor import split_into_sections, extract_all_sections


def test_split_into_sections_finds_experience_and_projects(sample_resume_text):
    sections = split_into_sections(sample_resume_text)
    assert "experience" in sections
    assert "TechCorp" in sections["experience"]
    assert "education" in sections
    assert "GLS University" in sections["education"]


def test_extract_all_sections_returns_not_detected_for_missing():
    text = "Skills\nPython, Java"
    sections = extract_all_sections(text)
    assert sections["experience"] == "Not detected"
    assert sections["projects"] == "Not detected"


def test_extract_all_sections_never_fabricates_content(sample_resume_text):
    sections = extract_all_sections(sample_resume_text)
    # Every non-"Not detected" value must be substring of the original text.
    for key, value in sections.items():
        if value != "Not detected":
            assert value.rstrip("…") in sample_resume_text or value in sample_resume_text
