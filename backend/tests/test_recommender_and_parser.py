from app.services.recommender import recommend_for_missing_skills
from app.services.resume_parser import extract_text, ExtractionError


def test_recommend_for_missing_skills_known_skill():
    recs = recommend_for_missing_skills(["Docker"])
    assert len(recs) == 1
    assert recs[0]["skill"] == "Docker"
    assert len(recs[0]["topics"]) > 0


def test_recommend_for_missing_skills_unknown_skill_gets_generic_recommendation():
    recs = recommend_for_missing_skills(["SomeObscureSkillXYZ"])
    assert len(recs) == 1
    assert recs[0]["skill"] == "SomeObscureSkillXYZ"
    assert recs[0]["level"] == "Beginner"


def test_recommend_for_missing_skills_empty_list():
    assert recommend_for_missing_skills([]) == []


def test_extract_text_unsupported_extension(tmp_path):
    bad_file = tmp_path / "resume.exe"
    bad_file.write_text("not a real resume")
    try:
        extract_text(bad_file)
        assert False, "Expected ExtractionError"
    except ExtractionError:
        pass


def test_extract_text_from_txt_file(tmp_path):
    txt_file = tmp_path / "jd.txt"
    txt_file.write_text("We are hiring a Python developer.")
    text = extract_text(txt_file)
    assert "Python developer" in text
