import os
import sys
from pathlib import Path

os.environ.setdefault("ENABLE_SEMANTIC_MODEL", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture
def sample_resume_text():
    return """John Doe
john.doe@example.com | +1-555-123-4567
linkedin.com/in/johndoe | github.com/johndoe

Summary
Backend engineer with experience building REST APIs using Python and FastAPI.

Skills
Python, FastAPI, SQL, PostgreSQL, Git, Docker, REST API, Machine Learning

Experience
Software Engineer Intern at TechCorp
- Developed and deployed REST APIs using Python and FastAPI
- Improved query performance by 40 percent using PostgreSQL indexing
- Automated deployment pipelines with Docker

Education
Bachelor of Technology in Computer Science, GLS University, 2026
"""


@pytest.fixture
def sample_jd_text():
    return """Job Title: Backend Software Engineer

Required:
- Strong experience with Python and FastAPI
- Experience with SQL and PostgreSQL
- Familiarity with Docker and AWS
- Bachelor's degree in Computer Science
- 2+ years of experience

Preferred:
- Experience with Kubernetes
- Knowledge of Machine Learning
"""
