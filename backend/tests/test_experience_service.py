from app.services.experience_service import (
    estimate_years_of_experience,
    experience_match_score,
    parse_experience_requirement,
)


def test_parses_year_ranges():
    req = parse_experience_requirement("Requires 2-5 years of cybersecurity experience")
    assert (req.min_years, req.max_years) == (2.0, 5.0)


def test_parses_floor_only_ranges():
    req = parse_experience_requirement("5+ years of experience")
    assert (req.min_years, req.max_years) == (5.0, 5.0)


def test_parses_to_range():
    req = parse_experience_requirement("Experience: 3 to 6 years of backend development")
    assert (req.min_years, req.max_years) == (3.0, 6.0)


def test_returns_none_without_requirement():
    assert parse_experience_requirement("We need a Python developer.") is None


def test_education_dates_are_not_counted_as_work_experience():
    """
    Regression risk: crediting a student's four-year degree as work experience
    is the classic way a screener inflates an inexperienced candidate.
    """
    resume = """
    Education
    B.Tech in Computer Science, Vellore Institute of Technology, 2022-2026, CGPA 8.7
    Higher Secondary, 2020-2022
    """
    result = estimate_years_of_experience(resume)
    assert result["years"] == 0.0


def test_counts_employment_date_ranges():
    resume = """
    Experience
    Backend Engineer, Acme Corp
    2020-2023
    Software Engineer, Globex
    Jan 2023 - Present
    """
    result = estimate_years_of_experience(resume)
    # 2020-2023 plus 2023-present, merged into one continuous stint.
    assert 6.0 < result["years"] < 7.0


def test_overlapping_roles_are_not_double_counted():
    """
    2021-2023 and 2022-2024 cover three calendar years between them. Summing
    the two stints naively would report four.
    """
    resume = """
    Experience
    Engineer, Acme, 2021-2023
    Consultant, Globex, 2022-2024
    """
    result = estimate_years_of_experience(resume)
    assert result["years"] == 3.0
    assert result["years"] < 2.0 + 2.0


def test_counts_single_year_internship():
    resume = """
    Experience
    Data Science Intern, Tech Startup (2024)
    - Built dashboards with Python
    """
    result = estimate_years_of_experience(resume)
    assert 0 < result["years"] <= 1.0


def test_ignores_bare_year_in_a_project_line():
    resume = """
    Projects
    Built a chatbot in 2023 using NLP and Python.
    """
    result = estimate_years_of_experience(resume)
    assert result["years"] == 0.0


def test_explicit_claim_takes_priority():
    resume = """
    Summary
    Backend engineer with 6 years of experience building APIs.
    Experience
    Engineer, Acme, 2023-2024
    """
    result = estimate_years_of_experience(resume)
    assert result["source"] == "explicit_claim"
    assert result["years"] == 6.0


def test_experience_match_is_floor_not_ceiling():
    """'2-5 years' is a hiring band, not a bar on the top of it."""
    req = parse_experience_requirement("2-5 years of experience")
    assert experience_match_score(2.0, req) == 100.0
    assert experience_match_score(7.0, req) == 100.0
    assert experience_match_score(0.0, req) == 0.0
    assert 0 < experience_match_score(1.0, req) < 50


def test_experience_match_is_none_when_not_measurable():
    assert experience_match_score(5.0, None) is None


def test_inexperienced_candidate_is_penalised_for_senior_role():
    student = estimate_years_of_experience(
        "Education\nB.Tech, Vellore Institute of Technology, 2022-2026"
    )
    senior = parse_experience_requirement("5-8 years of cloud architecture experience")
    junior = parse_experience_requirement("0-2 years of experience")

    assert experience_match_score(student["years"], senior) < experience_match_score(
        student["years"], junior
    )
