from datetime import datetime

from pydantic import BaseModel, Field


class JobDescriptionRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Raw job description text")


class JobDescriptionResponse(BaseModel):
    job_title: str | None
    required_skills: list[dict]
    preferred_skills: list[dict]
    all_skills: list[dict]
    education_requirement: str | None
    experience_requirement: str | None
    experience_min_years: float | None = None
    experience_max_years: float | None = None
    keywords: list[str]


class CandidateInfo(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    location: str | None
    linkedin: str | None
    github: str | None
    organizations: list[str] = []


class ScoreBreakdown(BaseModel):
    semantic_score: float
    tfidf_score: float
    skill_score: float
    keyword_score: float
    final_score: float
    used_semantic_model: bool
    weights: dict
    raw_semantic_score: float | None = None
    experience_score: float | None = None
    parseability_score: float | None = None
    categories: dict = {}
    keyword_detail: dict = {}
    parseability_detail: dict = {}


class KnockoutGate(BaseModel):
    label: str
    requirement: str
    requirement_met: bool
    detail: str


class KnockoutResult(BaseModel):
    """Hard minimums the job description states, kept out of the numeric score.

    A gate the job never states is not a failure, so `passed` is only False
    for a real, stated requirement the resume does not meet.
    """
    gates: list[KnockoutGate] = []
    failed: list[str] = []
    passed: bool = True
    evaluated: bool = False


class ExperienceInfo(BaseModel):
    years: float = 0.0
    source: str = "none"
    detail: str = ""
    required: str | None = None
    required_min_years: float | None = None
    required_max_years: float | None = None
    match_score: float | None = None


class QualityCheck(BaseModel):
    label: str
    passed: bool
    detail: str = ""


class CompatibilityIndicator(BaseModel):
    label: str
    ok: bool
    note: str = ""


class RecommendationItem(BaseModel):
    skill: str
    level: str
    topics: list[str]
    project_idea: str
    resource_hint: str


class AnalyzeResponse(BaseModel):
    id: int | None = None
    candidate: CandidateInfo
    job_title: str | None
    scores: ScoreBreakdown
    matched_skills: list[str]
    missing_skills: list[str]
    additional_skills: list[str]
    total_jd_skills: int
    summary: str
    sections: dict
    recommendations: list[RecommendationItem]
    quality: dict
    compatibility: dict
    knockouts: KnockoutResult = KnockoutResult()
    status: str
    created_at: datetime | None = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    matched_required: list[str] = []
    missing_required: list[str] = []
    matched_preferred: list[str] = []
    missing_preferred: list[str] = []
    experience: ExperienceInfo = ExperienceInfo()

    class Config:
        from_attributes = True


class AnalysisListItem(BaseModel):
    id: int
    candidate_name: str | None
    email: str | None
    resume_filename: str
    job_title: str | None
    final_score: float
    status: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class BulkCandidateResult(BaseModel):
    filename: str
    candidate_name: str | None
    final_score: float
    skills_matched: int
    missing_skills: int
    status: str
    error: str | None = None
