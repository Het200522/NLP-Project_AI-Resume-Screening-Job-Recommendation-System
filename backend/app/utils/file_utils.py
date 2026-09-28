import re
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from app.config import (
    UPLOAD_DIR, MAX_FILE_SIZE_BYTES, ALLOWED_RESUME_EXTENSIONS, ALLOWED_JD_EXTENSIONS,
)


def _safe_filename(original: str) -> str:
    stem = Path(original).stem
    suffix = Path(original).suffix
    safe_stem = re.sub(r"[^A-Za-z0-9_\-]", "_", stem)[:60]
    return f"{safe_stem}_{uuid.uuid4().hex[:8]}{suffix}"


async def save_upload(file: UploadFile, kind: str = "resume") -> Path:
    """
    Validates extension + size, then saves the file with a safe,
    collision-resistant filename inside the isolated uploads directory.
    """
    allowed = ALLOWED_RESUME_EXTENSIONS if kind == "resume" else ALLOWED_JD_EXTENSIONS
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(allowed))}",
        )

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the maximum allowed size.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(file.filename or "upload")
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(contents)

    return dest
