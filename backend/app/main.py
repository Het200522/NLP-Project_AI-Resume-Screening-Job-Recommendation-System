import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import CORS_ORIGINS
from app.database import init_db
from app.api import resume, job_description, analysis, candidates, reports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Resume Screening & Job Recommendation System",
    description="NLP-powered resume-to-job matching, skill gap analysis, and recruiter dashboard API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Load DB schema and warm up expensive NLP models once, not per-request."""
    init_db()
    logger.info("Database initialized.")

    # Warm up models so the first user request isn't slow.
    try:
        from app.services.similarity_service import _load_semantic_model
        _load_semantic_model()
        logger.info("Semantic model warm-up complete.")
    except Exception as e:
        logger.warning("Semantic model warm-up skipped: %s", e)

    try:
        from app.services.ner_service import _load_spacy
        _load_spacy()
        logger.info("spaCy model warm-up complete.")
    except Exception as e:
        logger.warning("spaCy model warm-up skipped: %s", e)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )


@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "ai-resume-screener-backend"}


app.include_router(resume.router)
app.include_router(job_description.router)
app.include_router(analysis.router)
app.include_router(candidates.router)
app.include_router(reports.router)
