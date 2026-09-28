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
        "Experience\nBuilt REST APIs using Python and FastAPI.\n\nEducation\nB.Tech Computer Science",
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
    assert "ats_score" in data["compatibility"]


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
