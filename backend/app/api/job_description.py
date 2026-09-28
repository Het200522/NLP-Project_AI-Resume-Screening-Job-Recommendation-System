from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from app.schemas.analysis import JobDescriptionRequest, JobDescriptionResponse
from app.services.jd_parser import parse_job_description
from app.services.resume_parser import extract_text, ExtractionError
from app.services.role_templates import list_roles, get_role
from app.utils.file_utils import save_upload

router = APIRouter(prefix="/api/job-description", tags=["job-description"])


@router.get("/roles")
async def get_roles():
    """List all available predefined role templates."""
    return list_roles()


@router.get("/roles/{role_id}")
async def get_role_template(role_id: str):
    """Get a specific role template's full job description."""
    role = get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found.")
    return {"id": role["id"], "title": role["title"], "description": role["description"]}


@router.post("/analyze", response_model=JobDescriptionResponse)
async def analyze_job_description(payload: JobDescriptionRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")
    result = parse_job_description(payload.text)
    return result


@router.post("/upload")
async def upload_job_description(file: UploadFile = File(...)):
    """Upload a TXT/PDF/DOCX job description and return its extracted text."""
    dest = await save_upload(file, kind="jd")
    try:
        text = extract_text(dest)
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"filename": dest.name, "text": text}
