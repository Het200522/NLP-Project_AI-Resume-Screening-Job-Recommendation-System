"""
section_extractor.py
Splits resume text into its standard sections (Experience, Projects,
Education, Skills, etc.) using heading-line detection, so the dashboard
can show actual extracted content rather than a simple presence check.

Heuristic, not a full layout parser -- works well on conventionally
formatted resumes (a heading on its own line), which covers the large
majority of real-world resumes.
"""
import re

SECTION_ALIASES = {
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "projects": ["projects", "personal projects", "academic projects", "portfolio"],
    "education": ["education", "academic background", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies"],
    "certifications": ["certifications", "certificates", "licenses"],
    "summary": ["summary", "professional summary", "objective", "profile"],
}

# Build a single lookup: alias text -> canonical section name
_ALIAS_TO_SECTION = {
    alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases
}

_MAX_SECTION_CHARS = 1200


def _is_heading_line(line: str) -> str | None:
    """Returns the canonical section name if this line looks like a section heading."""
    stripped = line.strip().strip(":").strip()
    if not stripped or len(stripped.split()) > 5:
        return None
    lower = stripped.lower()
    return _ALIAS_TO_SECTION.get(lower)


def split_into_sections(resume_text: str) -> dict[str, str]:
    """
    Returns {section_name: extracted_text} for every recognized section
    heading found in the resume. Sections not found are simply absent
    from the dict (never fabricated).
    """
    lines = resume_text.splitlines()
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in lines:
        heading = _is_heading_line(line)
        if heading:
            current_section = heading
            sections.setdefault(current_section, [])
            continue
        if current_section:
            sections[current_section].append(line)

    result = {}
    for name, content_lines in sections.items():
        text = "\n".join(content_lines).strip()
        # Trim to a reasonable display length without cutting mid-word.
        if len(text) > _MAX_SECTION_CHARS:
            text = text[:_MAX_SECTION_CHARS].rsplit(" ", 1)[0] + "…"
        if text:
            result[name] = text

    return result


def get_section(resume_text: str, section_name: str) -> str:
    """Returns extracted text for one section, or 'Not detected' if absent."""
    sections = split_into_sections(resume_text)
    return sections.get(section_name) or "Not detected"


def extract_all_sections(resume_text: str) -> dict[str, str]:
    """
    Returns a fixed set of section keys (experience, projects, education,
    certifications) each set to extracted text or 'Not detected'. Used to
    populate the resume analysis response.
    """
    sections = split_into_sections(resume_text)
    keys = ["experience", "projects", "education", "certifications"]
    return {k: sections.get(k) or "Not detected" for k in keys}
