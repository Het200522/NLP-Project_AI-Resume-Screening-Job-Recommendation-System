"""
Named Entity Recognition service.
Uses spaCy for PERSON / ORG / GPE / DATE, with regex-based supplementary
extraction for EMAIL and PHONE (spaCy's default NER doesn't reliably catch
these). Falls back gracefully if the spaCy model isn't installed.
"""
import re
import logging
from functools import lru_cache

from app.config import SPACY_MODEL

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(
    r"(?:(?:\+?\d{1,3})[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?){2,4}\d{2,4}"
)
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_/]+", re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_spacy():
    try:
        import spacy

        return spacy.load(SPACY_MODEL)
    except Exception as e:
        logger.warning(
            "spaCy model '%s' unavailable (%s). NER will fall back to regex-only extraction.",
            SPACY_MODEL,
            e,
        )
        return None


def _first_or_none(items: list[str]) -> str | None:
    return items[0] if items else None


def _valid_phone(candidate: str) -> bool:
    digits = re.sub(r"\D", "", candidate)
    return 7 <= len(digits) <= 15


# ── Technology / tool / framework names that spaCy often misclassifies ──
_TECH_WORDS = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "rust", "kotlin", "swift", "scala", "r", "matlab", "perl", "php",
    "html", "css", "sql", "nosql", "graphql", "solidity",
    # Frontend
    "react", "reactjs", "react.js", "angular", "angularjs", "vue", "vuejs",
    "vue.js", "next", "nextjs", "next.js", "nuxt", "nuxtjs", "svelte",
    "tailwind", "tailwindcss", "bootstrap", "jquery", "redux", "graphql",
    # Backend
    "node", "nodejs", "node.js", "express", "expressjs", "django", "flask",
    "fastapi", "fastapi", "spring", "springboot", "spring boot", "laravel",
    "rails", "ruby on rails", "asp.net", ".net", "dotnet",
    # Data / ML / AI
    "tensorflow", "tensorflow", "pytorch", "keras", "scikit-learn",
    "sklearn", "pandas", "numpy", "scipy", "matplotlib", "seaborn",
    "streamlit", "gradio", "huggingface", "hugging face", "spacy", "nltk",
    "opencv", "xgboost", "lightgbm", "catboost", "mlflow", "kubeflow",
    "langchain", "openai", "chatgpt", "gpt", "bert", "transformer",
    "transformers", "llama", "gemma", "mistral", "neural", "deep learning",
    "machine learning", "artificial intelligence", "ai", "nlp",
    "data science", "data scientist", "data analyst",
    # Cloud / DevOps
    "aws", "amazon web services", "gcp", "google cloud", "azure",
    "docker", "kubernetes", "k8s", "jenkins", "terraform", "ansible",
    "nginx", "apache", "linux", "ubuntu", "centos", "debian",
    "git", "github", "gitlab", "bitbucket", "ci/cd", "devops",
    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "firebase", "supabase", "prisma", "sqlite",
    "oracle", "mssql", "sql server",
    # Tools / Misc
    "figma", "sketch", "adobe", "photoshop", "illustrator",
    "jira", "confluence", "slack", "notion", "trello",
    "vscode", "visual studio", "intellij", "eclipse", "vim", "neovim",
    "postman", "swagger", "webpack", "vite", "babel", "eslint",
    "selenium", "cypress", "jest", "mocha", "pytest", "unittest",
    "rest", "restful", "rest api", "grpc", "websocket",
    "microservices", "serverless", "lambda", "cloudflare",
    "kafka", "rabbitmq", "celery", "redis",
    # Common resume words misclassified
    "objective", "summary", "profile", "about", "contact",
    "education", "experience", "skills", "projects", "certifications",
    "awards", "achievements", "publications", "references",
    "bachelor", "master", "phd", "b.tech", "m.tech", "bca", "mca", "mba",
    "b.e.", "m.e.", "b.s.", "m.s.", "b.sc.", "m.sc.",
    "gpa", "cgpa", "percentage",
    "full stack", "frontend", "backend", "devops", "site reliability",
    "data engineer", "data analyst", "data scientist",
    "software engineer", "software developer", "systems engineer",
    "cloud engineer", "network engineer", "security engineer",
    "product manager", "project manager", "scrum master",
    "ui/ux", "ui ux", "graphic designer",
    "intern", "internship", "fresher", "graduate",
    "team lead", "tech lead", "architect",
    "open source", "hackathon", "leetcode", "codechef", "codeforces",
}

# Regex patterns that are definitely NOT a person's name
_NON_NAME_RE = re.compile(
    r"(@|https?://|www\.|\.com|\.org|\.net|\.edu|\.in|\.io|"
    r"\d{4}|\d{3}[-.]?\d{3}[-.]?\d{4}|"
    r"[a-z]+@[a-z]|"
    r"^(?:yes|no|ok|na|n/a|none|null|undefined)$)",
    re.IGNORECASE,
)

# Section headers / resume structural keywords
_SECTION_KEYWORDS = re.compile(
    r"^(resume|cv|curriculum vitae|contact|education|experience|skills|projects|"
    r"summary|objective|profile|about|references|certifications|awards|"
    r"languages|interests|hobbies|declaration|personal|technical|"
    r"professional experience|work experience|employment|internship|"
    r"work history|key projects|academic|degree|university|college|"
    r"phone|email|address|linkedin|github|portfolio|website|"
    r"data scientist|software engineer|developer|manager|analyst|"
    r"full stack|frontend|backend|devops|machine learning|"
    r"b\.?tech|m\.?tech|bachelor|master|phd|bca|mca|mba|"
    r"Senior|Junior|Lead|Principal|Staff|Head of)",
    re.IGNORECASE,
)


def _is_tech_word(word: str) -> bool:
    """Check if a word is a known technology/tool/framework name."""
    return word.lower() in _TECH_WORDS


def _validate_name(name: str) -> bool:
    """
    Validate whether a string is plausibly a person's name.
    Returns False for tech terms, section headers, too-long strings, etc.
    """
    if not name or len(name) < 2:
        return False

    # Reject if contains digits
    if any(c.isdigit() for c in name):
        return False

    # Reject if matches a section header
    if _SECTION_KEYWORDS.match(name):
        return False

    # Reject if matches non-name patterns
    if _NON_NAME_RE.search(name):
        return False

    # Reject if too many words (names are typically 1-4 words)
    words = name.split()
    if len(words) > 4:
        return False

    # Reject if any word is a known tech term (case-insensitive)
    for w in words:
        if _is_tech_word(w):
            return False

    # Reject if any ALL-CAPS word is a known tech acronym
    # (but allow ALL-CAPS names like "HET SHAH" — very common in resumes)
    for w in words:
        if len(w) > 1 and w.isupper() and _is_tech_word(w):
            return False

    # Accept: each word should be alphabetic (with allowed punctuation like - ')
    for w in words:
        clean = w.replace("-", "").replace("'", "")
        if not clean:
            return False
        if not all(c.isalpha() or c in "-'" for c in clean):
            return False

    return True


def _extract_name_heuristic(text: str) -> str | None:
    """
    Heuristic name extraction from resume text. Checks the first N lines
    for a plausible candidate name, skipping section headers, contact info,
    and other non-name patterns.

    Strategy: The candidate's name is almost always in the first 5 lines
    of a resume, usually the very first non-empty line.
    """
    lines = text.splitlines()
    candidates = []

    for line in lines[:15]:
        line = line.strip()
        if not line:
            continue

        # Skip lines with emails, phones, URLs
        if EMAIL_RE.search(line) or PHONE_RE.search(line) or LINKEDIN_RE.search(line) or GITHUB_RE.search(line):
            continue

        # Skip section headers
        if _SECTION_KEYWORDS.match(line):
            continue

        # Skip lines that look like non-names
        if _NON_NAME_RE.search(line):
            continue

        words = line.split()

        # 2-4 word names (e.g. "John Smith", "Mary Jane Watson")
        if 2 <= len(words) <= 4:
            if _validate_name(line):
                candidates.append((line, 0))  # priority 0 = best

        # Single word names (e.g. "Priya")
        elif len(words) == 1:
            if _validate_name(line):
                candidates.append((line, 1))  # priority 1 = lower

        # If we found a good 2-4 word name, return it immediately
        if candidates and candidates[-1][1] == 0:
            return candidates[-1][0]

    if candidates:
        return candidates[0][0]

    return None


def extract_entities(text: str) -> dict:
    """
    Returns a dict of extracted candidate entities. Fields the system
    couldn't confidently extract are set to None (never fabricated).
    """
    result = {
        "name": None,
        "email": None,
        "phone": None,
        "location": None,
        "linkedin": None,
        "github": None,
        "organizations": [],
        "dates": [],
    }

    if not text:
        return result

    # Regex-based (reliable for structured contact info)
    emails = EMAIL_RE.findall(text)
    result["email"] = _first_or_none(emails)

    phone_candidates = [m.group(0) for m in PHONE_RE.finditer(text) if _valid_phone(m.group(0))]
    result["phone"] = _first_or_none(phone_candidates)

    linkedin = LINKEDIN_RE.findall(text)
    # Also detect bare "LinkedIn" mentions (without full URL)
    if not linkedin and re.search(r"\blinkedin\b", text, re.IGNORECASE):
        linkedin = ["LinkedIn"]
    result["linkedin"] = _first_or_none(linkedin)

    github = GITHUB_RE.findall(text)
    # Also detect bare "GitHub" mentions (without full URL)
    if not github and re.search(r"\bgithub\b", text, re.IGNORECASE):
        github = ["GitHub"]
    result["github"] = _first_or_none(github)

    # Run heuristic first — it's the most reliable for resume names
    heuristic_name = _extract_name_heuristic(text)

    # spaCy-based (name, org, location, dates)
    spacy_name = None
    nlp = _load_spacy()
    if nlp is not None:
        # Limit to first ~5000 chars for speed; names/orgs typically appear early.
        doc = nlp(text[:5000])
        persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
        orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
        locations = [ent.text.strip() for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
        dates = [ent.text.strip() for ent in doc.ents if ent.label_ == "DATE"]

        # Validate spaCy's PERSON detections against our tech blacklist
        valid_persons = [p for p in persons if _validate_name(p)]
        spacy_name = _first_or_none(valid_persons)

        result["organizations"] = list(dict.fromkeys(orgs))[:10]
        result["location"] = _first_or_none(locations)
        result["dates"] = list(dict.fromkeys(dates))[:10]

    # Priority: heuristic first (it's designed for resumes), then spaCy
    if heuristic_name:
        result["name"] = heuristic_name
    elif spacy_name:
        result["name"] = spacy_name

    return result
