# AI Resume Screening & Job Recommendation System

An NLP-powered web application that matches resumes against job descriptions, surfaces skill gaps, generates learning recommendations, and produces a single explainable ATS score — built for college placements, internships, recruiters, and HR teams.

## Overview

Upload a resume (PDF/DOCX) and a job description, and the system extracts candidate information, computes **one** unified ATS score, reports hard requirements as separate pass/fail gates, identifies matched/missing skills, generates a resume summary, and produces a downloadable PDF report. It also supports ranking multiple candidates against a single job description.

### One score, not two

Earlier versions of this project showed two independent scores side by side: a "match score" and an "ATS readiness score". They disagreed on the same resume — one panel reported contact completeness as 50% while the other reported 100%, and quantified achievements as 33% versus 100% — because two different regexes were measuring the same signals. Both models are now gone.

There is a single scoring engine (`similarity_service.py`) producing a single `final_score`, and the compatibility panel reports pass/fail indicators without a number.

## Problem Statement

Manually screening resumes against job requirements is slow, inconsistent, and hard to explain to candidates or hiring managers. This project demonstrates how NLP techniques (text preprocessing, NER, TF-IDF, sentence embeddings, skill-gap analysis) can produce a transparent, explainable resume-to-job matching score — explicitly *not* a claim to replicate any commercial ATS vendor's proprietary algorithm.

## Objectives

- Parse resumes and job descriptions from PDF/DOCX/TXT
- Extract candidate entities (name, email, phone, links) without fabricating missing data
- Extract and normalize technical/professional skills
- Compute a single, explainable ATS score dominated by job-description coverage
- Report hard requirements the job states (experience, degree, certifications) as separate pass/fail gates
- Identify skill gaps and recommend learning paths
- Support single-resume analysis and multi-resume ranking
- Generate downloadable PDF reports

## Features

- Drag-and-drop resume upload (PDF/DOCX), with automatic Tesseract OCR fallback for scanned/image-only PDFs
- Job description paste or upload (TXT/PDF/DOCX), plus 13 built-in role templates
- Resume summary generation (extractive, from actual resume content only)
- Matched / missing / additional skill detection with normalization (e.g. "ML" → "Machine Learning") over a 226-skill taxonomy
- **One unified ATS score** across five weighted categories, with every sub-score exposed (see [Scoring Model](#scoring-model))
- **Hard requirement gates** for minimum experience, degree level, and named certifications, reported as pass/fail and kept out of the score
- **Synonym and fuzzy keyword matching**, so "K8s" satisfies "Kubernetes" and a near-spelling ("Kubernets") still counts
- Experience estimation from employment date ranges, overlap-safe
- Skill-gap-based recommendations with topics and project ideas
- Multi-resume ranking table with sorting/filtering
- PDF report generation and download
- Recruiter dashboard with charts (Recharts)
- Cursor-following hover animation on dashboard cards

## Scoring Model

The score is deliberately dominated by requirement coverage, because that is the only part that changes between job postings. Weights live in `backend/app/config.py` and are environment-variable overridable.

| Category | Default | What it measures |
|---|---|---|
| `skill_match` | 40% | Share of the JD's skills present in the resume |
| `keyword_match` | 20% | JD keywords present, IDF-weighted, synonym + fuzzy aware |
| `semantic_match` | 15% | Sentence-embedding similarity, floor-calibrated |
| `experience_match` | 15% | Years of experience vs. the role's stated requirement |
| `parseability` | 10% | Whether an ATS can read the file at all |

`Final Score = Σ (weight × category_score)`, renormalized across the categories that could be evaluated. A category with no applicable input (for example `experience_match` when the JD states no requirement) reports `null` and its weight is redistributed, so scores stay comparable on a 0–100 scale.

**Parseability** is the only resume-only signal, and it is sub-weighted: contact completeness 30%, section structure 25%, formatting risk 25%, length/structure 20%. It answers "can a parser extract this text", not "is this candidate good".

### Scoring choices worth knowing

- **Skills are scored flat** — `matched JD skills / total JD skills`, every skill weighted equally. An earlier version weighted required skills 60% and preferred skills 40%, which is a recruiter heuristic, not ATS behavior.
- **Semantic scores are calibrated** — sentence embeddings place two *unrelated* professional documents at roughly 0.35–0.50 cosine similarity, so an uncalibrated score handed ~45/100 to a completely mismatched candidate. The usable band `[40, 75]` is rescaled onto 0–100.
- **Keyword overlap uses background IDF** — a corpus of job descriptions determines how distinctive each term is, so filler that appears in every posting ("experience", "skills", "best") counts for far less than a role-specific term ("siem", "kubernetes").
- **Requirements are not a percentage** — see below.

## Hard Requirement Gates (Knockouts)

A posting that says "5+ years of Kubernetes experience" or "Masters degree required" is stating a *filter*, not a preference. Real ATS platforms ask these minimum-qualification questions **before** ranking anyone; Greenhouse and Lever expose them as explicit gate questions, and a candidate who fails one is either not surfaced or ranked last regardless of the rest of the profile.

`backend/app/services/knockout.py` evaluates three gate types:

| Gate | Triggered when the JD states... |
|---|---|
| Minimum experience | A years-of-experience requirement in a hard-requirement context |
| Minimum education | A degree level alongside "required", "must have", "essential", "minimum" |
| Required certification | A named certification (CKA, AWS Certified, CISSP, PMP, …) in a hard-requirement context |

**A failed gate does not lower the numeric score.** This is deliberate. Folding a gate into the weighted average would bury the reason a candidate was filtered — they'd see a slightly lower number and never learn they were missing a mandatory certification. Instead the gate verdict is reported alongside the score, so the output explains itself.

A posting that states no hard minimums reports `evaluated: false` and never fails. A passing mention of a degree ("bachelor's degree holders do great here") is not treated as a requirement.

## NLP Concepts Demonstrated

| Concept | Where |
|---|---|
| Text preprocessing (clean → tokenize → lowercase → stopwords → lemmatize) | `app/services/preprocess.py` |
| OCR fallback for scanned PDFs (Tesseract via pytesseract, 300 DPI) | `app/services/resume_parser.py` |
| Named Entity Recognition (spaCy + regex fallback) | `app/services/ner_service.py` |
| Skill extraction with alias normalization | `app/services/skill_extractor.py` |
| TF-IDF + cosine similarity | `app/services/similarity_service.py` |
| Sentence embeddings (all-MiniLM-L6-v2) + cosine similarity | `app/services/similarity_service.py` |
| Semantic score calibration to a usable band | `app/services/similarity_service.py` |
| Background-corpus IDF for keyword weighting | `app/services/similarity_service.py` |
| Synonym canonicalization + fuzzy token matching | `app/services/keyword_matcher.py` |
| Overlap-safe experience estimation from date ranges | `app/services/experience_service.py` |
| Rule-based knockout (hard requirement) detection | `app/services/knockout.py` |
| Extractive summarization | `app/services/summarizer.py` |
| Rule-based recommendation engine | `app/services/recommender.py` |
| Weighted multi-factor scoring (single engine) | `app/services/similarity_service.py` |

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
Skill Extraction (resume + JD)   ·   Experience Estimation (overlap-safe date ranges)
        ↓
Knockout Gate Evaluation (experience · degree · certifications)
        ↓
Unified ATS Score
  skill 40% · keywords 20% · semantic 15% · experience 15% · parseability 10%
        ↓
Recommendations + Resume Summary + Compatibility Indicators
        ↓
Results Dashboard + Downloadable PDF Report
```

The knockout gates are evaluated alongside the score but never added to it — see [Hard Requirement Gates](#hard-requirement-gates-knockouts).

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
│   │   ├── services/
│   │   │   ├── analysis_orchestrator.py  # Pipeline
│   │   │   ├── analysis_reader.py        # Rebuilds a saved analysis
│   │   │   ├── similarity_service.py     # THE scoring engine
│   │   │   ├── keyword_matcher.py        # Synonym + fuzzy matching
│   │   │   ├── knockout.py               # Hard requirement gates
│   │   │   ├── experience_service.py     # Date-range experience estimate
│   │   │   ├── ats_checker.py            # Parseability signals + quality checks
│   │   │   ├── skill_extractor.py, jd_parser.py, ner_service.py,
│   │   │   ├── preprocess.py, summarizer.py, recommender.py,
│   │   │   ├── section_extractor.py, resume_parser.py,
│   │   │   ├── report_generator.py, resume_improver.py, role_templates.py
│   │   ├── models/              # SQLAlchemy models
│   │   └── schemas/            # Pydantic schemas
│   ├── data/
│   │   ├── skills.csv          # 226-skill taxonomy with aliases
│   │   └── course_recommendations.csv
│   ├── sample_data/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── docker-compose.yml
└── README.md
```

## Configuration

All tunables live in `backend/app/config.py` and are environment-variable overridable. Scoring weights are asserted to sum to 1.0 at import time, so a bad override fails loudly rather than silently changing the scale.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | SQLite file | Point at PostgreSQL to switch databases |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `MAX_FILE_SIZE_MB` | `10` | Upload size limit |
| `ENABLE_SEMANTIC_MODEL` | `true` | Set `false` to skip the embedding model entirely |
| `SENTENCE_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `ATS_SKILL_WEIGHT` | `0.40` | JD skill coverage |
| `ATS_KEYWORD_WEIGHT` | `0.20` | Keyword coverage |
| `ATS_SEMANTIC_WEIGHT` | `0.15` | Semantic relevance |
| `ATS_EXPERIENCE_WEIGHT` | `0.15` | Experience fit |
| `ATS_PARSEABILITY_WEIGHT` | `0.10` | Parser readability |
| `ATSP_CONTACT_WEIGHT` | `0.30` | Sub-weight: contact completeness |
| `ATSP_SECTION_WEIGHT` | `0.25` | Sub-weight: section structure |
| `ATSP_FORMATTING_WEIGHT` | `0.25` | Sub-weight: formatting risk |
| `ATSP_LENGTH_WEIGHT` | `0.20` | Sub-weight: length/structure |
| `SEMANTIC_FLOOR` | `40` | Cosine at or below this maps to 0 |
| `SEMANTIC_CEILING` | `75` | Cosine at or above this maps to 100 |

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

Only the data directory is mounted as a volume, so **source changes are not picked up by a restart** — they require a rebuild:

```bash
docker compose build
docker compose up -d
```

> Compose has no source bind mount, so editing Python or TypeScript and running `docker compose up -d` alone will silently keep serving the old code. Always rebuild.

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

### Scoring fields in the response

```jsonc
{
  "scores": {
    "final_score": 74.61,          // the single ATS score
    "skill_score": 100.0,
    "keyword_score": 50.47,
    "semantic_score": 33.71,       // calibrated onto 0-100
    "raw_semantic_score": 46.9,    // uncalibrated cosine
    "experience_score": 69.44,
    "parseability_score": 90.48,
    "used_semantic_model": true,
    "categories": {                // null = not applicable for this role
      "skill_match": 100.0, "keyword_match": 50.47, "semantic_match": 33.71,
      "experience_match": 69.44, "parseability": 90.48
    },
    "weights": { /* the five weights actually used */ },
    "keyword_detail":    { "keywords": [], "matched": [], "missing": [], "fuzzy_matches": [] },
    "parseability_detail": { "contact_info": 100.0, "section_structure": 100.0, "formatting": 100.0, "length": 52.4 }
  },
  "compatibility": { "indicators": [ /* pass/fail only, deliberately no score */ ] },
  "knockouts": {
    "evaluated": true,
    "passed": false,
    "failed": ["Minimum experience", "Required certification"],
    "gates": [
      { "label": "Minimum experience", "requirement": "6+ years", "requirement_met": false, "detail": "..." }
    ]
  }
}
```

There is no `ats_score` field anywhere in the response — a second, competing score was removed because it contradicted the main one.

## NLP Methodology

**One score, composed of five weighted categories.** The formula is `Final Score = Σ (weight × category_score)`, with the weights in `backend/app/config.py` (defaults 40/20/15/15/10, all env-overridable, asserted to sum to 1.0). The rationale behind the split is in [Scoring Model](#scoring-model).

**Skill matching (40%)** — a flat share: `matched JD skills / total JD skills`, every skill weighted equally. Skills come from a 226-entry CSV taxonomy with alias lists (e.g. "ML" → "Machine Learning") matched using whole-word/phrase regex, never naive substring matching, to avoid false positives on short tokens.

**Keyword matching (20%)** — the JD's most distinctive terms are ranked by `IDF × frequency` using a background corpus of job descriptions, then the resume is checked for them. Matching is synonym-aware and fuzzy-tolerant, the way commercial ATS keyword search is: "k8s" satisfies "kubernetes" and a near-spelling still counts. Without this a candidate loses real points for using the term their industry actually uses. A comparison budget caps fuzzy comparisons so a very long resume cannot slow scoring down.

**Semantic matching (15%)** — `all-MiniLM-L6-v2` (via `sentence-transformers`) encodes the full resume and JD into dense vectors and compares them with cosine similarity, capturing paraphrase that lexical methods miss. Raw cosine is then **calibrated**: embeddings place two unrelated professional documents at roughly 0.35–0.50 similarity, so the usable band `[SEMANTIC_FLOOR, SEMANTIC_CEILING]` (40–75 by default) is rescaled onto 0–100. Without this a fully mismatched candidate scored ~45/100. If the model can't be loaded (e.g. no network at runtime), the system falls back to TF-IDF for this component.

**Experience matching (15%)** — years are estimated from employment date ranges with overlap-safe merging (concurrent roles are not double-counted), then compared against the requirement parsed from the JD. If the JD states no requirement, this category reports `null` and its weight is redistributed.

**Parseability (10%)** — can a parser read this file: contact completeness, section structure, formatting risk, and length. It is the only resume-only signal in the score, capped at 10% for that reason. The previous "ATS readiness" model spent 70% of its weight on hygiene and only 30% on the job itself, so a resume with zero skill overlap but tidy formatting scored around 70.

**NER** — spaCy's `en_core_web_sm` model extracts PERSON, ORG, GPE, and DATE entities. Because spaCy's default model isn't reliable for structured fields, EMAIL and PHONE are extracted via regex as a supplementary method.

**Knockout gates** — hard minimums stated by the job (experience, degree, named certifications) are detected and evaluated as pass/fail, reported separately from the score so a filter is never hidden inside an average.

**A note on proprietary systems** — this is an independent, rule-based model built on publicly documented resume-parsing and ATS behavior. It does not and cannot reproduce Workday, Taleo, Greenhouse, or any other vendor's undisclosed algorithm.

## Testing

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

69 tests across 9 files. Beyond the basics (skill extraction and false-positive avoidance, preprocessing, section extraction, parser error handling, recommendations), the suite pins down the scoring behaviour that was previously wrong:

| Regression guarded | File |
|---|---|
| Role discrimination — a resume must not score similarly across unrelated roles | `test_role_discrimination.py` |
| The score is monotonic in requirement coverage | `test_similarity.py` |
| Skills are scored flat, not 60:40 required/preferred | `test_similarity.py` |
| Only one score exists — no second `ats_score` leaking out of the engine | `test_similarity.py` |
| Synonym ("k8s") and fuzzy ("Kubernets") matches count | `test_similarity.py` |
| Unscored categories redistribute weight instead of scoring zero | `test_similarity.py` |
| Parseability goes up for clean, machine-readable resumes | `test_similarity.py` |
| Section score divides by the right number of sections | `test_similarity.py` |
| Semantic calibration maps the unusable band to zero | `test_similarity.py` |
| Gates only trigger on *stated* requirements, not passing mentions | `test_knockout.py` |
| Failed gates do not silently change the score | `test_knockout.py` |
| A posting with no hard minimums never fails | `test_knockout.py` |
| A saved analysis round-trips with the same breakdown and gates as the live response | `test_api.py` |
| Full PDF pipeline through `/api/analyze` and PDF report generation | `test_api.py` |

The test environment disables the sentence-transformer model for speed; `test_similarity.py` exercises the calibration function directly to cover that path.

## Known Limitations

- **The score is an independent estimate**, not a prediction of how any specific ATS product will rank a resume — those algorithms are proprietary and undisclosed, so no implementation can legitimately claim parity. It models publicly documented behavior: rank on requirement coverage, treat parser readability as a prerequisite, filter stated minimums.
- **Knockout gate detection is regex-based.** It reliably catches explicit phrasing ("required", "must have", "8+ years") and will miss a requirement stated indirectly ("you'll have led a team"). A missed gate means a false pass, not a false rejection, so the failure mode is permissive.
- **Synonym matching is a curated dictionary**, not learned. It covers common industry equivalents (k8s/Kubernetes, JS/JavaScript) and will not know an unusual one. Fuzzy matching is deliberately conservative and bounded by a comparison budget, so it can miss a heavily misspelled term rather than risk false matches.
- **Semantic model availability**: if `sentence-transformers` can't download its model weights at runtime (no internet), semantic scoring falls back to the TF-IDF score. Set `ENABLE_SEMANTIC_MODEL=false` to skip attempting the download entirely.
- **Section/experience/project extraction** is heuristic (regex + keyword-based), not a full resume-structure parser — it works well on conventionally formatted resumes but may miss heavily custom layouts.
- **Scanned/image-only PDFs** are handled by falling back to Tesseract OCR (`pytesseract` + the `tesseract-ocr` system package, installed in the backend Dockerfile). When a PDF has no embedded text layer, `resume_parser.py` renders each page at 300 DPI and OCRs it. OCR accuracy on low-quality scans is limited, and if a page yields no text the request fails with a clear error rather than fabricating content.
- **Stored analyses keep their original score.** `final_score` is persisted at analysis time; a saved analysis shows the breakdown and gates recomputed from stored text, but the headline number reflects the model version current when it was run. Re-analyze to rescore under newer weights.
- **SQLite** is used for simplicity; the SQLAlchemy layer is structured so swapping in PostgreSQL only requires changing `DATABASE_URL`.

## Future Enhancements

- PostgreSQL/Supabase support for production deployments
- Recruiter authentication and multi-user accounts
- Cloud deployment (AWS/Azure/GCP)
- Deeper resume-section extraction (dedicated experience/project parsers)
- Learned synonym expansion so matching isn't limited to a curated dictionary
- LLM-assisted explanations of match scores
- Expanded, community-maintained skills dataset
