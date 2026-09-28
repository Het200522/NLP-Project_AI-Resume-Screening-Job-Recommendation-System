from app.services.preprocess import clean_text, preprocess_for_matching


def test_clean_text_removes_bullets_and_excess_whitespace():
    raw = "•  Built  an API\n\n\n\nUsed Python"
    cleaned = clean_text(raw)
    assert "•" not in cleaned
    assert "Built" in cleaned
    assert "\n\n\n\n" not in cleaned


def test_preprocess_for_matching_lowercases_and_removes_stopwords():
    result = preprocess_for_matching("The Quick Brown Fox is running in the park")
    tokens = result.split()
    assert "the" not in tokens
    assert "is" not in tokens
    assert "quick" in tokens or "quick" in result


def test_preprocess_for_matching_handles_empty_string():
    assert preprocess_for_matching("") == ""
