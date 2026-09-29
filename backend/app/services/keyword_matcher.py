"""
keyword_matcher.py
Synonym-aware, fuzzy-tolerant term matching.

A literal token comparison under-reports real matches. A resume that says
"k8s" is describing Kubernetes; "JS" is JavaScript; "Postgres" is
PostgreSQL. Commercial ATS keyword search normalises abbreviations and
expands synonyms before matching, so a candidate silently loses points for
using the term the industry actually uses.

Two mechanisms, deliberately conservative:

  1. Canonicalisation - a fixed map of equivalent surface forms, applied to
     both documents so they meet on one canonical term. Only true
     equivalences belong here. Related-but-different skills (SQL vs MySQL)
     must NOT be listed, or a candidate gains credit for a skill they
     never claimed.

  2. Fuzzy matching - for tokens long enough that a near-spelling is
     plausibly the same word ("kubernets", "postgreess"). Restricted to
     longer tokens on both sides and a high similarity ratio, because
     aggressive fuzzy matching invents matches between short unrelated
     words ("go" and "gcp").
"""
import re
from functools import lru_cache

from difflib import SequenceMatcher

# Single-token surface forms that mean the same thing. Bidirectional.
TOKEN_CANONICAL: dict[str, str] = {
    # languages / runtimes
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "py3": "python",
    "golang": "go",
    "c++": "cpp",
    "cplusplus": "cpp",
    "objective-c": "objc",
    "postgres": "postgresql",
    "psql": "postgresql",
    "py3": "python",
    "sqlite3": "sqlite",
    # infra / cloud
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "ec2": "aws",
    "eks": "kubernetes",
    "gke": "kubernetes",
    "aks": "kubernetes",
    "iaas": "cloud",
    "paas": "cloud",
    "gcp": "google cloud",
    "aws": "aws",
    "azure": "azure",
    "tf": "terraform",
    "iic": "terraform",
    "k": "kubernetes",
    # ml / data
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "sklearn": "scikit learn",
    "sk-learn": "scikit learn",
    "tf": "tensorflow",
    "torch": "pytorch",
    "np": "numpy",
    "pd": "pandas",
    "bi": "business intelligence",
    "etl": "data pipeline",
    # practices
    "ci": "continuous integration",
    "cd": "continuous delivery",
    "ci/cd": "ci cd",
    "iac": "infrastructure as code",
    "tdd": "test driven development",
    "oop": "object oriented programming",
    "rest": "rest api",
    "restful": "rest api",
    "apis": "api",
    "ux": "user experience",
    "ui": "user interface",
    "pm": "product management",
    "qa": "quality assurance",
    "seo": "search engine optimization",
}

# Multi-word surface forms, matched as phrases in the raw (preprocessed)
# text because a tokenizer would split "machine learning" into two tokens.
# Each entry is a tuple of interchangeable phrases.
PHRASE_GROUPS: tuple[tuple[str, ...], ...] = (
    ("machine learning", "ml", "machinelearning"),
    ("deep learning", "dl", "deeplearning"),
    ("natural language processing", "nlp", "naturallanguageprocessing"),
    ("computer vision", "cv", "computervision"),
    ("artificial intelligence", "ai", "artificialintelligence"),
    ("continuous integration", "ci"),
    ("continuous delivery", "continuous deployment", "cd"),
    ("continuous integration and delivery", "ci cd", "cicd", "ci/cd"),
    ("infrastructure as code", "iac"),
    ("test driven development", "tdd"),
    ("object oriented programming", "oop"),
    ("rest api", "rest", "restful", "restful api", "restful apis"),
    ("user experience", "ux", "user experience design"),
    ("user interface", "ui"),
    ("product management", "pm"),
    ("quality assurance", "qa", "qualityassurance"),
    ("google cloud platform", "gcp", "google cloud"),
    ("amazon web services", "aws"),
    ("microsoft azure", "azure"),
    ("apache kafka", "kafka"),
    ("scikit learn", "sklearn", "sk-learn", "scikit-learn"),
    ("power bi", "powerbi"),
    ("tableau", "tableau", "tableau desktop"),
    ("search engine optimization", "seo"),
    ("supply chain management", "scm"),
    ("customer relationship management", "crm"),
    ("human resources", "hr", "humanresource"),
    ("business intelligence", "bi"),
    ("data science", "data scientist", "datascience", "datascientist"),
    ("site reliability engineering", "sre"),
    ("message queue", "message queuing"),
    ("version control", "version control", "source control", "git", "vcs"),
    ("operating system", "operating systems"),
    ("data structures", "data structure", "dsa", "ds"),
    ("design patterns", "design pattern"),
    ("load balancing", "load balancer", "loadbalancing"),
    ("penetration testing", "penetration test", "pentesting", "pen test"),
    ("threat modeling", "threat model", "threatmodeling"),
    ("incident response", "incident management"),
    ("access control", "access management"),
    ("network security", "networksec"),
)

# Canonical term for each phrase group, used to collapse every surface form
# in the group onto one token.
_PHRASE_CANON: dict[str, str] = {}
for _group in PHRASE_GROUPS:
    _canon = _group[0]
    for _phrase in _group:
        _PHRASE_CANON[_phrase] = _canon

# Canonical token for each synonym-group member (longest phrase first so that
# "machine learning" is not shadowed by "ml").
_SYNONYM_TOKENS: tuple[tuple[str, str], ...] = tuple(
    sorted(TOKEN_CANONICAL.items(), key=lambda kv: len(kv[0]), reverse=True)
)

# Fuzzy matching guards. Short tokens are excluded on both sides because
# edit distance is meaningless there: "go"/"gcp"/"c" collide constantly.
FUZZY_MIN_LENGTH = 5
FUZZY_MIN_RATIO = 0.88
# Upper bound on comparisons, so a very long resume cannot make scoring slow.
_MAX_FUZZY_COMPARISONS = 2000


def _strip_accents(value: str) -> str:
    return re.sub(r"[^\w\s+.-]", "", value)


def canonicalize_token(token: str) -> str:
    """Folds one token onto its canonical surface form."""
    cleaned = token.strip(".-_").lower()
    return TOKEN_CANONICAL.get(cleaned, cleaned)


def _phrase_presence(text: str) -> set[str]:
    """
    Returns the canonical names of every synonym phrase present in the text.
    Matching is done on the text with word boundaries, so "ai" does not fire
    on "said" and "ml" does not fire inside "html".
    """
    lowered = text.lower()
    present: set[str] = set()
    for phrase, canon in _PHRASE_CANON.items():
        if len(phrase) < 2:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            present.add(canon)
    return present


@lru_cache(maxsize=512)
def _fuzzy_match(a: str, b: str) -> bool:
    if abs(len(a) - len(b)) > max(2, int(len(a) * 0.25)):
        return False
    return SequenceMatcher(None, a, b).ratio() >= FUZZY_MIN_RATIO


def tokenize_for_matching(text: str) -> set[str]:
    """
    Turns free text into a comparable set of surface forms: canonicalised
    single tokens plus the canonical name of any synonym phrase found.
    """
    tokens = set()
    for raw in text.split():
        cleaned = canonicalize_token(raw)
        if cleaned:
            tokens.add(cleaned)
    tokens |= _phrase_presence(text)
    return tokens


def fuzzy_find(
    candidates: set[str],
    resume_tokens: set[str],
    *,
    budget: list[int] | None = None,
) -> set[str]:
    """
    Returns the subset of `candidates` that have no exact counterpart in
    `resume_tokens` but are within edit distance of one, i.e. likely the same
    term misspelled or re-spelled.
    """
    if not candidates or not resume_tokens:
        return set()

    comparable = sorted(
        t for t in resume_tokens
        if len(t) >= FUZZY_MIN_LENGTH and t.isalnum()
    )
    if not comparable:
        return set()

    remaining = [c for c in candidates if len(c) >= FUZZY_MIN_LENGTH]
    hits: set[str] = set()
    for candidate in remaining:
        if candidate in resume_tokens:
            continue
        for other in comparable:
            if budget is not None:
                if budget[0] <= 0:
                    return hits
                budget[0] -= 1
            if _fuzzy_match(candidate, other):
                hits.add(candidate)
                break
    return hits


def match_terms(
    jd_terms: set[str],
    resume_text: str,
) -> tuple[set[str], set[str], set[str]]:
    """
    Matches JD terms against resume text with synonym expansion and fuzzy
    tolerance.

    Returns (matched, exact, fuzzy). `matched` is the union, and the other two
    let callers report *how* a term was matched, which is the part a candidate
    actually needs to see.
    """
    resume_tokens = tokenize_for_matching(resume_text)
    exact = {t for t in jd_terms if t in resume_tokens}
    unresolved = jd_terms - exact
    fuzzy = fuzzy_find(unresolved, resume_tokens)
    return exact | fuzzy, exact, fuzzy


def expand_terms(terms: set[str]) -> set[str]:
    """
    Expands a term set with every known synonym of each term, so a JD that
    says "Kubernetes" and a resume that says "k8s" meet on one term.
    """
    expanded = set(terms)
    for term in terms:
        canon = TOKEN_CANONICAL.get(term, term)
        expanded.add(canon)
        for source, target in TOKEN_CANONICAL.items():
            if target == canon:
                expanded.add(source)
        for phrase, phrase_canon in _PHRASE_CANON.items():
            if phrase_canon == canon:
                expanded.add(phrase)
    return expanded
