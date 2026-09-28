from fastapi import APIRouter, UploadFile, File, HTTPException

from app.utils.file_utils import save_upload
from app.services.resume_parser import extract_text, ExtractionError

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    Uploads a resume (PDF/DOCX), validates it, and returns a preview of the
    extracted text plus the stored path for use in /api/analyze.
    """
    dest = await save_upload(file, kind="resume")

    try:
        text = extract_text(dest)
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {
        "filename": dest.name,
        "original_filename": file.filename,
        "path": str(dest),
        "size_bytes": dest.stat().st_size,
        "preview": text[:400],
        "word_count": len(text.split()),
    }
