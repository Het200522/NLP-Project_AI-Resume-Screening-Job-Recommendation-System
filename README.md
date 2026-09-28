# AI Resume Screening & Job Recommendation System

An NLP-powered web application that matches resumes against job descriptions, surfaces skill gaps, generates learning recommendations, and produces a real-world-style ATS readiness score — built for college placements, internships, recruiters, and HR teams.

## Overview

Upload a resume (PDF/DOCX) and a job description, and the system extracts candidate information, computes an explainable match score using both TF-IDF and sentence-embedding similarity, identifies matched/missing skills, generates a resume summary, and produces a downloadable PDF report. It also supports ranking multiple candidates against a single job description.

## Problem Statement

Manually screening resumes against job requirements is slow, inconsistent, and hard to explain to candidates or hiring managers. This project demonstrates how NLP techniques (text preprocessing, NER, TF-IDF, sentence embeddings, skill-gap analysis) can produce a transparent, explainable resume-to-job matching score — explicitly *not* a claim to replicate any commercial ATS vendor's proprietary algorithm.

## Objectives

- Parse resumes and job descriptions from PDF/DOCX/TXT
- Extract candidate entities (name, email, phone, links) without fabricating missing data
- Extract and normalize technical/professional skills
- Score resume-job fit using both lexical (TF-IDF) and semantic (sentence-transformer) similarity
- Identify skill gaps and recommend learning paths
- Provide a transparent, weighted ATS readiness score
- Support single-resume analysis and multi-resume ranking
- Generate downloadable PDF reports

## Features

- Drag-and-drop resume upload (PDF/DOCX)
- Job description paste or upload (TXT/PDF/DOCX)
- Resume summary generation (extractive, from actual resume content only)
- Matched / missing / additional skill detection with normalization (e.g. "ML" → "Machine Learning")
- Combined match score: `Final Score = 60% Semantic Similarity + 40% Skill Match` (configurable)
- Real-world-style, weighted ATS readiness score across 7 categories (keyword match, section structure, contact completeness, quantifiable achievements, action-verb usage, formatting risk, length)
- Skill-gap-based recommendations with topics and project ideas
- Multi-resume ranking table with sorting/filtering
- PDF report generation and download
- Recruiter dashboard with charts (Recharts)
- Cursor-following hover animation on dashboard cards

## NLP Concepts Demonstrated

| Concept | Where |
|---|---|
| Text preprocessing (clean → tokenize → lowercase → stopwords → lemmatize) | `app/services/preprocess.py` |
| Named Entity Recognition (spaCy + regex fallback) | `app/services/ner_service.py` |
| Skill extraction with alias normalization | `app/services/skill_extractor.py` |
| TF-IDF + cosine similarity | `app/services/similarity_service.py` |
| Sentence embeddings (all-MiniLM-L6-v2) + cosine similarity | `app/services/similarity_service.py` |
| Extractive summarization | `app/services/summarizer.py` |
| Rule-based recommendation engine | `app/services/recommender.py` |
| Weighted multi-factor ATS scoring | `app/services/ats_checker.py` |

## System Architecture

```
Next.js (React + TypeScript) ──HTTP/JSON──▶ FastAPI (Python)
                                                  │
                                    ┌─────────────┼─────────────┐
                                    ▼             ▼             ▼
                            resume_parser   NLP services   SQLite (SQLAlchemy)
                            (PyMuPDF/docx)  (spaCy, sklearn,
                                             sentence-transformers)
```

## Workflow

```
Upload Resume + Job Description
        ↓
Text Extraction (PyMuPDF / python-docx)
        ↓
NLP Preprocessing (clean, tokenize, lemmatize)
        ↓
NER (candidate name, email, phone, links)
        ↓
Skill Extraction (resume + JD)
        ↓
TF-IDF Similarity  +  Sentence Embedding Similarity
        ↓
Skill Gap Analysis (matched / missing / additional)
        ↓
Weighted Final Score
        ↓
Recommendations + Resume Summary + ATS Readiness Score
        ↓
Results Dashboard + Downloadable PDF Report
```

## Technology Stack

**Frontend:** Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS, Recharts, Axios, Sonner, Lucide React

**Backend:** FastAPI, Uvicorn, Pydantic, SQLAlchemy, SQLite

**NLP/ML:** spaCy, NLTK, scikit-learn, sentence-transformers, pandas, numpy

**File processing:** PyMuPDF (PDF), python-docx (DOCX)

**Reports:** ReportLab

**Testing:** pytest, httpx

## Folder Structure

```
AI-Resume-Screener/
├── frontend/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx            # Landing page
│   │   ├── dashboard/
│   │   ├── analyze/
│   │   ├── candidates/
│   │   ├── reports/
│   │   └── settings/
│   ├── components/             # Reusable UI components
│   ├── lib/api.ts              # Centralized API client
│   └── .env.example
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint
│   │   ├── config.py           # Central config (scoring weights, limits)
│   │   ├── database.py
│   │   ├── api/                # Route handlers
│   │   ├── services/           # NLP pipeline + business logic
│   │   ├── models/              # SQLAlchemy models
│   │   └── schemas/            # Pydantic schemas
│   ├── data/
│   │   ├── skills.csv
│   │   └── course_recommendations.csv
│   ├── sample_data/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── docker-compose.yml
└── README.md
```

## Installation

### Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

> NLTK resources (punkt, stopwords, wordnet) are downloaded automatically on first run. If your environment has no internet access at runtime, the system falls back to a lightweight built-in stopword list and regex-based tokenization — it still works, just with slightly less refined preprocessing.

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # adjust NEXT_PUBLIC_API_URL if needed
npm run dev
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### Docker Setup

```bash
cp .env.example .env
docker compose up --build
```

This runs the frontend on http://localhost:3000 and the backend on http://localhost:8080 (container port 8000). The backend Dockerfile downloads the spaCy model and NLTK resources at build time.

`NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` are set in a `.env` file next to `docker-compose.yml`:

- **`NEXT_PUBLIC_API_URL`** is inlined into the frontend bundle at *build* time, so it is the URL the **browser** uses — not a Docker service name like `http://backend:8000`. When you open the app from another machine, set it to the host's LAN IP or domain (e.g. `http://192.168.1.10:8080`) and rebuild with `docker compose up --build`, since changing it requires a rebuild.
- **`CORS_ORIGINS`** must contain the exact origin you open the frontend on. If it doesn't, the browser blocks the API responses and dropdowns such as "Select Role" render empty.

A common symptom of either one being wrong is the "Select Role" dropdown showing only "Choose a role..." with no options. Open the browser console/network tab — the app now surfaces the failing URL and error instead of silently showing an empty list.

## API Documentation

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/resume/upload` | Upload and preview-extract a resume |
| POST | `/api/job-description/analyze` | Parse a pasted job description |
| POST | `/api/job-description/upload` | Upload a JD file (TXT/PDF/DOCX) |
| POST | `/api/analyze` | Full resume vs. JD analysis (multipart: `resume` file + `job_description` text) |
| GET | `/api/analysis/{id}` | Retrieve a saved analysis |
| GET | `/api/analysis/{id}/report` | Download the PDF report |
| DELETE | `/api/analysis/{id}` | Delete an analysis |
| POST | `/api/candidates/bulk-analyze` | Analyze multiple resumes against one JD |
| GET | `/api/candidates` | List all past analyses, ranked by score |

Full interactive documentation is available at `/docs` (Swagger UI) once the backend is running.

## NLP Methodology

**TF-IDF + Cosine Similarity** — a baseline lexical similarity: both texts are preprocessed, vectorized with `TfidfVectorizer`, and compared with cosine similarity. Fast, explainable, but purely lexical (misses synonyms).

**Sentence Embeddings** — `all-MiniLM-L6-v2` (via `sentence-transformers`) encodes the full resume and JD into dense vectors capturing semantic meaning, then compares them with cosine similarity. Captures paraphrasing and synonymy that TF-IDF misses. If the model can't be loaded (e.g. no network at runtime), the system gracefully falls back to the TF-IDF score for this component.

**Combined Score** — `Final Score = SEMANTIC_WEIGHT × semantic_score + SKILL_WEIGHT × skill_score`, configurable via environment variables in `backend/app/config.py` (defaults: 60% / 40%).

**NER** — spaCy's `en_core_web_sm` model extracts PERSON, ORG, GPE, and DATE entities. Because spaCy's default model isn't reliable for structured fields, EMAIL and PHONE are extracted via regex as a supplementary method.

**Skill Extraction** — a CSV-backed skill database (`backend/data/skills.csv`) with alias lists (e.g. "ML" → "Machine Learning") is matched against text using whole-word/phrase regex matching — never naive substring matching — to avoid false positives.

**ATS Readiness Score** — a transparent, weighted score across 7 categories (keyword match, section structure, contact completeness, quantifiable achievements, action-verb usage, formatting risk, length). This is an independent, rule-based model built on publicly documented resume-parsing best practices — it does not and cannot claim to reproduce any specific ATS vendor's undisclosed proprietary algorithm.

## Testing

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

25 tests cover: skill extraction (including false-positive avoidance), preprocessing, TF-IDF similarity, the recommendation engine, file parsing error handling, section extraction (experience/projects/education), and full API integration flows (including a real generated PDF through `/api/analyze`).

## Known Limitations

- **Semantic model availability**: if `sentence-transformers` can't download its model weights at runtime (no internet), semantic scoring falls back to the TF-IDF score. Set `ENABLE_SEMANTIC_MODEL=false` to skip attempting the download entirely.
- **Section/experience/project extraction** is heuristic (regex + keyword-based), not a full resume-structure parser — it works well on conventionally formatted resumes but may miss heavily custom layouts.
- **ATS score is an independent estimate**, not a guarantee of how any specific real-world ATS product will score a resume — no legitimate implementation can claim otherwise, since those algorithms are proprietary and undisclosed.
- **Scanned/image-only PDFs** are not OCR'd; text extraction will fail gracefully with a clear error rather than fabricating content.
- **SQLite** is used for simplicity; the SQLAlchemy layer is structured so swapping in PostgreSQL only requires changing `DATABASE_URL`.

## Future Enhancements

- PostgreSQL/Supabase support for production deployments
- Recruiter authentication and multi-user accounts
- Cloud deployment (AWS/Azure/GCP)
- Deeper resume-section extraction (dedicated experience/project parsers)
- LLM-assisted explanations of match scores
- Expanded, community-maintained skills dataset
