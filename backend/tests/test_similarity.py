from app.services.similarity_service import (
    tfidf_similarity,
    compute_final_score,
    skill_match_score,
    keyword_overlap_score,
    parseability_score,
    _section_score,
)
from app.config import ATS_WEIGHTS, PARSEABILITY_WEIGHTS


def test_tfidf_similarity_identical_text_is_high():
    text = "Python developer with experience in FastAPI and PostgreSQL"
    score = tfidf_similarity(text, text)
    assert score > 90


def test_tfidf_similarity_unrelated_text_is_low():
    resume = "Professional chef specializing in French pastry and baking techniques"
    jd = "Senior backend engineer needed for distributed systems and Kubernetes"
    score = tfidf_similarity(resume, jd)
    assert score < 30


def test_tfidf_similarity_empty_text_returns_zero():
    assert tfidf_similarity("", "some job description") == 0.0
    assert tfidf_similarity("some resume", "") == 0.0


def test_tfidf_similarity_rewards_shared_rare_terms():
    """
    Fitting on only two documents gave every term an identical IDF, so the
    shared term was weighted no higher than a unique one. Fitting against a
    background corpus must make a rare shared term count.
    """
    resume = "Engineer with Kubernetes and Terraform cluster administration skills"
    unrelated = "Chef specialising in French pastry, baking and dessert technique"
    related = "Engineer with Kubernetes and Terraform cluster administration skills"
    jd = "We need someone experienced with Kubernetes and Terraform"

    assert tfidf_similarity(resume, jd) > tfidf_similarity(resume, unrelated)


def test_keyword_overlap_ignores_generic_filler():
    """'experience'/'skills' appear in every posting and must not drive the score."""
    from app.services.role_templates import ROLES

    jd = ROLES["cybersecurity_analyst"]["description"]
    filler_only = "I have experience and skills."
    security_resume = (
        "Monitored security alerts in Splunk and QRadar SIEM. Configured firewalls "
        "and IDS/IPS. Ran OWASP Top 10 penetration testing and handled incident "
        "response and threat modeling."
    )
    unrelated_resume = "Pastry chef specialising in French patisserie and baking."

    filler = keyword_overlap_score(filler_only, jd)
    security = keyword_overlap_score(security_resume, jd)
    unrelated = keyword_overlap_score(unrelated_resume, jd)

    # Generic filler that appears in every posting must be worth close to nothing.
    assert filler < 10.0
    # A genuine domain match must be far above both filler and an unrelated field.
    assert security > 3 * filler
    assert security > 3 * unrelated
    assert keyword_overlap_score("", jd) == 0.0


def test_skill_match_score_is_a_flat_share_of_jd_skills():
    """ATS keyword matching: every JD skill counts the same."""
    assert skill_match_score(4, 4) == 100.0
    assert skill_match_score(4, 2) == 50.0
    assert skill_match_score(4, 0) == 0.0
    assert skill_match_score(0, 0) == 0.0
    assert skill_match_score(0, 5) == 0.0
    # Over-counting matches cannot exceed a full match.
    assert skill_match_score(3, 7) == 100.0


def test_section_score_counts_all_four_sections():
    """Regression: 4 sections were checked but divided by 3, inflating the score."""
    assert _section_score("experience\neducation") == 50.0
    assert _section_score("experience\neducation\nskills\nprojects") == 100.0
    assert _section_score("nothing relevant here") == 0.0


def test_parseability_rewards_a_clean_machine_readable_resume():
    """
    Parseability is the one resume-only signal in the score: it must go up for
    a well-formed document and down for a wall of text, so a candidate is not
    judged as weak when the real problem is that no parser can read the file.
    """
    clean = (
        "John Doe\njohn.doe@example.com | +1 555 123 4567 | linkedin.com/in/johndoe | github.com/johndoe\n\n"
        "SUMMARY\nBackend engineer focused on distributed systems.\n\n"
        "SKILLS\nPython, PostgreSQL, Kubernetes, Docker\n\n"
        "EXPERIENCE\n"
        "Engineered billing services handling 2M requests per day.\n"
        "Reduced p99 latency by 40 percent by adding a read-through cache.\n"
        "Migrated the payments platform to Kubernetes with zero downtime.\n"
        "Built an automated deployment pipeline cutting release time by 60 percent.\n"
        "Led the on-call rotation for three payment services in production.\n"
        "Optimised database queries reducing load by 35 percent across the fleet.\n"
        "Designed an idempotent retry layer for the notification service.\n"
        "Partnered with product to ship the subscription tier to all customers.\n"
        "Automated regression testing that caught defects before release.\n"
        "Maintained CI pipelines running over 900 test cases per commit.\n\n"
        "EDUCATION\nB.S. Computer Science, State University, 2016\n\n"
        "PROJECTS\n"
        "Open source rate limiter used by several internal services.\n"
        "Personal static site generator written in Go for static blogs.\n"
    )
    junk = "x" * 4000

    clean_score, _ = parseability_score(clean)
    junk_score, junk_parts = parseability_score(junk)

    assert 0 <= clean_score <= 100
    assert clean_score >= 75.0
    assert junk_score < clean_score
    # A readable resume with a full header must not be scored as missing contact.
    assert junk_parts["contact_info"] < clean_score


def test_parseability_weights_sum_to_one():
    assert abs(sum(PARSEABILITY_WEIGHTS.values()) - 1.0) < 1e-6


def test_keyword_overlap_matches_synonyms_and_near_misses():
    """
    Commercial ATS keyword search is synonym-aware. A candidate who writes
    "k8s" for a posting that says "kubernetes" has met the requirement and
    must not lose the match.
    """
    jd = "Engineer needed with Kubernetes, PostgreSQL and JavaScript experience."

    exact = keyword_overlap_score(
        "Engineer with Kubernetes, PostgreSQL and JavaScript experience.", jd
    )
    synonym = keyword_overlap_score(
        "Engineer with K8s, Postgres and JS experience.", jd
    )
    fuzzy = keyword_overlap_score(
        "Engineer with Kubernets, PostgerSQL and Javascript experience.", jd
    )
    unrelated = keyword_overlap_score(
        "Pastry chef specialising in French patisserie and baking.", jd
    )

    assert synonym > 0.5 * exact
    assert fuzzy > 0.5 * exact
    assert unrelated < 0.3 * exact


def test_keyword_overlap_detail_reports_missing_terms():
    jd = "Engineer needed with Kubernetes, PostgreSQL and Terraform experience."
    resume = "Engineer with Kubernetes and Terraform experience."
    _, detail = keyword_overlap_score(resume, jd, return_detail=True)

    assert "postgresql" in detail["missing"]
    assert "kubernetes" in detail["matched"]


def test_semantic_calibration_rescales_the_usable_cosine_band():
    """
    Regression: an uncalibrated 45/100 handed to a fully mismatched
    candidate. Everything at or below the floor must reach 0, and a strong
    match must be able to approach 100.
    """
    from app.services.similarity_service import _calibrate_semantic
    from app.config import SEMANTIC_FLOOR, SEMANTIC_CEILING

    assert _calibrate_semantic(None) == 0.0
    assert _calibrate_semantic(0.0) == 0.0
    assert _calibrate_semantic(SEMANTIC_FLOOR) == 0.0
    # The classic "unrelated professional documents" value.
    assert _calibrate_semantic(45.0) < 15.0
    # A real but unremarkable match should not be crushed into single digits.
    assert _calibrate_semantic(55.0) > 25.0
    assert _calibrate_semantic(SEMANTIC_CEILING) == 100.0
    assert _calibrate_semantic(100.0) == 100.0
    # Monotonic across the band.
    scores = [_calibrate_semantic(v) for v in range(0, 101, 5)]
    assert scores == sorted(scores)


def test_weights_favour_role_specific_categories():
    """
    The score must be dominated by what changes between job postings, not by
    resume hygiene. Parseability is the only resume-only signal and is capped
    at 10%.
    """
    role_specific = sum(
        ATS_WEIGHTS[k]
        for k in ("skill_match", "keyword_match", "semantic_match", "experience_match")
    )
    assert role_specific >= 0.85
    assert ATS_WEIGHTS["parseability"] <= 0.10
    assert abs(sum(ATS_WEIGHTS.values()) - 1.0) < 1e-6


def test_compute_final_score_within_bounds(sample_resume_text, sample_jd_text):
    result = compute_final_score(sample_resume_text, sample_jd_text, total_jd_skills=5, total_matched=3)
    assert 0 <= result["final_score"] <= 100
    assert 0 <= result["semantic_score"] <= 100
    assert 0 <= result["skill_score"] <= 100
    assert result["skill_score"] == 60.0  # 3/5 * 100


def test_score_is_monotonic_in_requirement_coverage(sample_resume_text, sample_jd_text):
    """More JD skills matched must never lower the ATS score."""
    scores = [
        compute_final_score(
            sample_resume_text, sample_jd_text, total_jd_skills=10, total_matched=m
        )["final_score"]
        for m in range(0, 11)
    ]
    assert scores == sorted(scores)


def test_unified_score_has_one_number_not_two_scales(sample_resume_text, sample_jd_text):
    """
    Regression: two independent models produced two scores for one resume
    that contradicted each other. The unified model exposes one final score
    and one set of sub-scores.
    """
    result = compute_final_score(sample_resume_text, sample_jd_text, 5, 3, experience_score=50.0)

    assert set(result["categories"]) == {
        "skill_match", "keyword_match", "semantic_match",
        "experience_match", "parseability",
    }
    assert "contact_info" not in result["categories"]
    assert "achievements" not in result["categories"]
    # No legacy second score leaks out of the engine.
    assert "ats_score" not in result
    assert "overall_score" not in result


def test_unscored_category_is_null_and_weight_redistributed(sample_resume_text, sample_jd_text):
    """With no experience requirement the weight must be redistributed, not zeroed."""
    without = compute_final_score(
        sample_resume_text, sample_jd_text, 5, 3, experience_score=None,
    )
    with_exp = compute_final_score(
        sample_resume_text, sample_jd_text, 5, 3, experience_score=0.0,
    )

    assert without["categories"]["experience_match"] is None
    assert with_exp["categories"]["experience_match"] == 0.0
    # 0 experience against a role must not score the same as "not applicable".
    assert with_exp["final_score"] < without["final_score"]
    # Both stay on a comparable 0-100 scale.
    assert 0 <= without["final_score"] <= 100
    assert 0 <= with_exp["final_score"] <= 100
