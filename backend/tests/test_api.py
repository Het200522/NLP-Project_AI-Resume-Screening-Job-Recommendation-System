import io

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_analyze_rejects_unsupported_file_type(client):
    resp = client.post(
        "/api/analyze",
        files={"resume": ("resume.exe", io.BytesIO(b"fake content"), "application/octet-stream")},
        data={"job_description": "We need a Python developer with FastAPI experience."},
    )
    assert resp.status_code == 400


def test_analyze_rejects_empty_job_description(client):
    resp = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
        data={},
    )
    assert resp.status_code == 422


def test_analyze_full_flow_with_pdf(client, tmp_path):
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Jane Smith\njane.smith@example.com\n555-000-1111\n\nSkills\nPython, FastAPI, SQL, Docker\n\n"
        "Experience\nBackend Engineer, Acme (2021-2023)\nBuilt REST APIs using Python and FastAPI.\n\n"
        "Education\nB.Tech Computer Science",
        fontsize=11,
    )
    pdf_path = tmp_path / "resume.pdf"
    doc.save(str(pdf_path))

    with open(pdf_path, "rb") as f:
        resp = client.post(
            "/api/analyze",
            files={"resume": ("resume.pdf", f, "application/pdf")},
            data={"job_description": "Looking for a Python developer with FastAPI and SQL experience."},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] is not None
    assert data["candidate"]["email"] == "jane.smith@example.com"
    assert "Python" in data["matched_skills"]
    assert 0 <= data["scores"]["final_score"] <= 100
    # One unified score: compatibility must not carry a second competing one.
    assert "ats_score" not in data["compatibility"]
    assert set(data["scores"]["categories"]) == {
        "skill_match", "keyword_match", "semantic_match",
        "experience_match", "parseability",
    }
    assert "knockouts" in data
    assert set(data["knockouts"]) >= {"gates", "failed", "passed", "evaluated"}

    # The new scoring fields must be present on the live response.
    for key in ("raw_semantic_score", "experience_score", "categories", "weights",
                "parseability_score", "keyword_detail", "parseability_detail"):
        assert key in data["scores"], f"scores.{key} missing"
    for key in ("matched_required", "missing_required", "matched_preferred", "missing_preferred"):
        assert key in data, f"{key} missing"
    assert set(data["experience"]) >= {
        "years", "source", "detail", "required", "required_min_years", "match_score"
    }
    assert data["experience"]["years"] > 0


def test_stored_analysis_reports_derived_fields_on_read_back(client, tmp_path):
    """A saved analysis must round-trip with tiers and experience intact."""
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Jane Smith\njane.smith@example.com\n\nSkills\nPython, SQL\n\n"
        "Experience\nSoftware Engineer, Acme (2021-2023)\nBuilt REST APIs.",
        fontsize=11,
    )
    pdf_path = tmp_path / "resume_roundtrip.pdf"
    doc.save(str(pdf_path))

    with open(pdf_path, "rb") as f:
        created = client.post(
            "/api/analyze",
            files={"resume": (pdf_path.name, f, "application/pdf")},
            data={"job_description": "Python developer with SQL and API experience."},
        )
    assert created.status_code == 200
    analysis_id = created.json()["id"]

    fetched = client.get(f"/api/analysis/{analysis_id}")
    assert fetched.status_code == 200
    data = fetched.json()

    assert data["id"] == analysis_id
    assert data["matched_skills"] == created.json()["matched_skills"]
    assert data["missing_required"] == created.json()["missing_required"]
    assert data["experience"]["years"] == created.json()["experience"]["years"]
    # TF-IDF is recomputed, so it must not be aliased to the semantic score.
    assert data["scores"]["tfidf_score"] != data["scores"]["semantic_score"] or not data[
        "scores"
    ]["used_semantic_model"]

    # A saved analysis must show the same unified breakdown and gates the live
    # endpoint returned, not an empty category map and a missing gate section.
    live = created.json()
    assert data["scores"]["categories"].keys() == live["scores"]["categories"].keys()
    for key, value in live["scores"]["categories"].items():
        if value is None:
            continue
        assert abs(data["scores"]["categories"][key] - value) < 0.5, key
    assert data["knockouts"] == live["knockouts"]
    assert "ats_score" not in data["compatibility"]


def test_scoring_config_endpoint_matches_live_weights(client):
    """
    Regression: the settings page hardcoded a 7-category weight table that had
    already been deleted from the backend, so the UI described a model that no
    longer existed. The endpoint must report exactly what the engine uses.
    """
    from app.config import ATS_WEIGHTS, PARSEABILITY_WEIGHTS

    resp = client.get("/api/scoring/config")
    assert resp.status_code == 200
    data = resp.json()

    assert data["weights"] == ATS_WEIGHTS
    assert data["parseability_weights"] == PARSEABILITY_WEIGHTS
    assert abs(sum(data["weights"].values()) - 1.0) < 1e-6
    # The one-score contract: no legacy category may reappear.
    assert "contact_info" not in data["weights"]
    assert "achievements" not in data["weights"]
    assert "knockouts_note" in data


def test_job_description_analyze_endpoint(client):
    resp = client.post(
        "/api/job-description/analyze",
        json={"text": "Job Title: Data Scientist\nRequired: Python, Machine Learning, SQL"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_title"] == "Data Scientist"
    assert any(s["skill"] == "Python" for s in data["all_skills"])


def test_candidates_list_endpoint(client):
    resp = client.get("/api/candidates")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
