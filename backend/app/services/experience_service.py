"""
experience_service.py

Turns "2-5 years of cybersecurity experience" and the date ranges on a resume
into comparable numbers, so a final-year student applying to a role that
requires five years of experience is actually penalized for it.

The candidate-side estimate deliberately ignores *education* date ranges --
otherwise every student is credited with their full degree duration as
"work experience", which is the single most common way a resume screener
inflates an inexperienced candidate.
"""
import re
from dataclasses import dataclass

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

_EDUCATION_MARKERS = re.compile(
    r"\b(university|college|institute|school|b\.?tech|m\.?tech|b\.?sc|m\.?sc|"
    r"bachelor|master|doctor|ph\.?d|degree|cgpa|gpa|class of|graduat|"
    r"board|intermediate|high school|secondary|diploma)\b",
    re.IGNORECASE,
)

_MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))

# "Jan 2021 - Mar 2023" | "January 2021 – Present" | "2021/06 to 2023/08"
_DATE_RANGE = re.compile(
    rf"(?:\b(?P<m1>{_MONTH_ALT})\b[\s.,]*)?(?P<y1>(?:19|20)\d{{2}})"
    rf"\s*(?:-|–|—|to|until|through|thru)\s*"
    rf"(?:\b(?P<m2>{_MONTH_ALT})\b[\s.,]*)?(?P<y2>(?:19|20)\d{{2}}|present|current|ongoing|now)\b",
    re.IGNORECASE,
)

# "5+ years of experience" / "3 years hands-on experience"
_EXPLICIT_YEARS = re.compile(
    r"\b(\d{1,2})\s*(?:\+|plus)?\s*(?:-|–|to)?\s*\d{0,2}\s*"
    r"(?:\+\s*)?years?\b[^.\n]{0,40}?\bexperience\b",
    re.IGNORECASE,
)

_MONTH_YEAR = re.compile(
    rf"^\s*(?P<mon>{_MONTH_ALT})\s+(?P<year>(?:19|20)\d{{2}})\s*$",
    re.IGNORECASE,
)

# A job title, used to recognise single-year stints such as
# "Data Science Intern, Acme (2024)" which carry a year but no range.
_ROLE_WORD = re.compile(
    r"\b(intern|internship|engineer|developer|analyst|scientist|manager|"
    r"consultant|designer|architect|administrator|specialist|associate|"
    r"assistant|technician|researcher|fellow|freelance|contractor|lead|"
    r"officer|executive|director|head of|founder|coordinator|programmer|"
    r"tester|qa|writer|editor|accountant|recruiter)\b",
    re.IGNORECASE,
)

_LONE_YEAR = re.compile(r"(?<![\d/])(?:19|20)\d{2}(?![\d/])")

# Conservative: credit a single-year listing as a fraction of a year rather
# than a full one, since a summer internship is not twelve months of work.
_SINGLE_STINT_YEARS = 0.75

_MAX_PLAUSIBLE_YEARS = 40.0

CURRENT_YEAR = 2026


@dataclass
class ExperienceRequirement:
    raw: str
    min_years: float
    max_years: float


def parse_experience_requirement(text: str) -> ExperienceRequirement | None:
    """
    Extracts a structured year range from JD text.

    "2-5 years of experience" -> min 2.0, max 5.0
    "3+ years"                -> min 3.0, max 3.0 (treated as a floor)
    "up to 5 years"           -> min 0.0, max 5.0
    """
    if not text:
        return None

    m = re.search(
        r"((?:\d{1,2}\s*(?:-|–|—|to)\s*)?\d{1,2}\s*(?:\+|plus)?)\s*"
        r"(?:\+\s*)?years?",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None

    raw = m.group(0).strip()
    body = m.group(1)

    rng = re.search(r"(\d{1,2})\s*(?:-|–|—|to)\s*(\d{1,2})", body)
    if rng:
        lo, hi = float(rng.group(1)), float(rng.group(2))
        if lo > hi:
            lo, hi = hi, lo
        return ExperienceRequirement(raw=raw, min_years=lo, max_years=hi)

    single = re.search(r"(\d{1,2})", body)
    if not single:
        return None
    years = float(single.group(1))
    if re.search(r"\bup to\b", text[max(0, m.start() - 12): m.start()], re.IGNORECASE):
        return ExperienceRequirement(raw=raw, min_years=0.0, max_years=years)
    return ExperienceRequirement(raw=raw, min_years=years, max_years=years)


def _month_of(name: str | None, year: int) -> float:
    """
    A month is expressed as a decimal year so two dates can be subtracted
    directly, e.g. March 2023 -> 2023 + 2/12.
    """
    if not name:
        return float(year)
    return year + (MONTHS.get(name.lower(), 1) - 1) / 12.0


def _end_point(year_token: str, month_token: str | None) -> float | None:
    if re.match(r"^(?:19|20)\d{2}$", year_token):
        year = int(year_token)
        if month_token:
            # End of the named month.
            return year + MONTHS.get(month_token.lower(), 12) / 12.0
        # A bare end year is treated as the start of that year, which is the
        # conservative reading of a resume range like "2020-2023" (~3 years).
        return float(year)
    # present / current / ongoing / now
    return CURRENT_YEAR + 0.5


def _merge(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1] + 0.04:  # treat adjacent roles as continuous
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return [(s, e) for s, e in merged]


def _estimate_from_ranges(text: str) -> float:
    intervals: list[tuple[float, float]] = []
    stints = 0

    for line in text.splitlines():
        if _EDUCATION_MARKERS.search(line):
            continue

        for m in _DATE_RANGE.finditer(line):
            start = _month_of(m.group("m1"), int(m.group("y1")))
            end = _end_point(m.group("y2"), m.group("m2"))
            if end is None or end <= start:
                continue
            # Reject implausible spans (typos, birth years, future dates).
            if end - start > 40:
                continue
            intervals.append((start, end))

        # Single-year listings such as "Data Science Intern, Acme (2024)".
        if not _DATE_RANGE.search(line):
            year_match = _LONE_YEAR.search(line)
            role_match = _ROLE_WORD.search(line)
            if year_match and role_match and role_match.start() < year_match.start():
                year = int(year_match.group(0))
                if 1980 <= year <= CURRENT_YEAR:
                    stints += 1

    years = sum(e - s for s, e in _merge(intervals))
    years += stints * _SINGLE_STINT_YEARS
    return round(min(years, _MAX_PLAUSIBLE_YEARS), 2)


def estimate_years_of_experience(resume_text: str) -> dict:
    """
    Estimates a candidate's relevant work experience in years.

    Sources, in priority order:
      1. An explicit "N years of experience" claim.
      2. Employment date ranges, ignoring education ranges and merging
         overlapping roles so concurrent jobs are not double counted.

    Returns {"years": float, "source": str, "detail": str}.
    """
    if not resume_text:
        return {"years": 0.0, "source": "none", "detail": "No experience information found."}

    from app.services.section_extractor import split_into_sections

    sections = split_into_sections(resume_text)
    experience_block = sections.get("experience")

    explicit = _EXPLICIT_YEARS.search(resume_text)
    if explicit:
        years = float(explicit.group(1))
        return {
            "years": years,
            "source": "explicit_claim",
            "detail": f"Resume explicitly claims {years:g} year(s) of experience.",
        }

    # Prefer the experience section; fall back to the whole document minus
    # the education section so internships still count.
    if experience_block:
        years = _estimate_from_ranges(experience_block)
        if years > 0:
            return {
                "years": years,
                "source": "date_ranges",
                "detail": f"{years:g} year(s) derived from employment date ranges.",
            }

    remainder = resume_text
    if sections.get("education"):
        remainder = resume_text.replace(sections["education"], " ")

    years = _estimate_from_ranges(remainder)
    if years > 0:
        return {
            "years": years,
            "source": "date_ranges",
            "detail": f"{years:g} year(s) derived from employment date ranges.",
        }

    return {
        "years": 0.0,
        "source": "none",
        "detail": "No employment date ranges detected; treated as 0 years of experience.",
    }


def experience_match_score(
    candidate_years: float, requirement: ExperienceRequirement | None
) -> float | None:
    """
    0-100 score for meeting a role's experience requirement, or None when
    the JD states no requirement (in which case the weight is redistributed
    rather than scored as zero).

    A range like "2-5 years" is treated as a floor: 2+ years is a full match,
    since employers hire at the bottom of their own posted band. Overqualifying
    is not penalized. Below the floor the score falls off proportionally.
    """
    if requirement is None:
        return None

    floor = requirement.min_years
    if floor <= 0:
        return 100.0

    if candidate_years >= floor:
        return 100.0

    # Partial credit that decays steeply: half the required experience is
    # worth far less than half the score.
    ratio = candidate_years / floor
    return round(max(0.0, (ratio ** 2)) * 100, 2)
