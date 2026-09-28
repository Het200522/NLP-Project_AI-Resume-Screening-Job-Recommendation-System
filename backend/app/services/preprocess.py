"""
NLP preprocessing pipeline:
Text Cleaning -> Tokenization -> Lowercasing -> Stopword Removal -> Lemmatization
"""
import re
import logging

logger = logging.getLogger(__name__)

_NLTK_READY = False
_lemmatizer = None
_stopwords = None


def _ensure_nltk():
    """Lazily download/load NLTK resources exactly once."""
    global _NLTK_READY, _lemmatizer, _stopwords
    if _NLTK_READY:
        return
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer

        for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"]:
            try:
                nltk.data.find(f"tokenizers/{pkg}") if "punkt" in pkg else nltk.data.find(
                    f"corpora/{pkg}"
                )
            except LookupError:
                try:
                    nltk.download(pkg, quiet=True)
                except Exception as e:
                    logger.warning("Could not download NLTK package %s: %s", pkg, e)

        _stopwords = set(stopwords.words("english"))
        _lemmatizer = WordNetLemmatizer()
        _NLTK_READY = True
    except Exception as e:
        logger.warning("NLTK unavailable, falling back to lightweight preprocessing: %s", e)
        _stopwords = _FALLBACK_STOPWORDS
        _lemmatizer = None
        _NLTK_READY = True


# Small fallback stopword list used only if NLTK resources can't be loaded
# (e.g. no network access at runtime).
_FALLBACK_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "is", "are", "was",
    "were", "be", "been", "being", "of", "to", "in", "on", "for", "with",
    "as", "by", "at", "from", "that", "this", "these", "those", "it", "its",
    "i", "you", "he", "she", "we", "they", "them", "his", "her", "their",
    "our", "your", "my", "me", "us", "not", "no", "so", "do", "does", "did",
    "have", "has", "had", "will", "would", "can", "could", "should", "may",
    "might", "must", "shall", "about", "into", "over", "after", "before",
}


def clean_text(text: str) -> str:
    """Remove control chars, excess whitespace, and normalize unicode dashes/bullets."""
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"[•●▪◦‣]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    _ensure_nltk()
    try:
        import nltk

        return nltk.word_tokenize(text)
    except Exception:
        return re.findall(r"[A-Za-z0-9+#\.\-]+", text)


def preprocess_for_matching(text: str) -> str:
    """
    Full pipeline used before TF-IDF / embedding comparison:
    clean -> tokenize -> lowercase -> stopword removal -> lemmatize -> rejoin.
    """
    _ensure_nltk()
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)

    processed = []
    for tok in tokens:
        tok_lower = tok.lower()
        if not re.match(r"^[a-z0-9+#\.\-]+$", tok_lower):
            continue
        if tok_lower in _stopwords:
            continue
        if len(tok_lower) < 2:
            continue
        if _lemmatizer:
            try:
                tok_lower = _lemmatizer.lemmatize(tok_lower)
            except Exception:
                pass
        processed.append(tok_lower)

    return " ".join(processed)
