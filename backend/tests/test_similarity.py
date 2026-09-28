from app.services.similarity_service import tfidf_similarity, compute_final_score


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


def test_compute_final_score_within_bounds(sample_resume_text, sample_jd_text):
    result = compute_final_score(sample_resume_text, sample_jd_text, total_jd_skills=5, total_matched=3)
    assert 0 <= result["final_score"] <= 100
    assert 0 <= result["semantic_score"] <= 100
    assert 0 <= result["skill_score"] <= 100
    assert result["skill_score"] == 60.0  # 3/5 * 100
