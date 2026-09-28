"""
summarizer.py
Generates a concise extractive resume summary using TF-IDF sentence
scoring (no external LLM calls, no fabricated content -- built only from
what's actually in the resume text).
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer


def _split_sentences(text: str) -> list[str]:
    # Lightweight sentence splitter (avoids depending on NLTK punkt at
    # summarization time specifically, though it's used elsewhere).
    candidates = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in candidates if len(s.strip().split()) >= 4]


def generate_summary(resume_text: str, entities: dict, skills: list[dict], max_sentences: int = 4) -> str:
    sentences = _split_sentences(resume_text)

    if not sentences:
        return "Not detected"

    if len(sentences) <= max_sentences:
        top_sentences = sentences
    else:
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            matrix = vectorizer.fit_transform(sentences)
            scores = matrix.sum(axis=1).A1
            ranked_idx = sorted(
                range(len(sentences)), key=lambda i: scores[i], reverse=True
            )[:max_sentences]
            ranked_idx.sort()  # preserve original order
            top_sentences = [sentences[i] for i in ranked_idx]
        except ValueError:
            top_sentences = sentences[:max_sentences]

    summary = " ".join(top_sentences)

    prefix_parts = []
    if entities.get("name"):
        prefix_parts.append(entities["name"])
    if skills:
        top_skills = ", ".join(s["skill"] for s in skills[:5])
        prefix_parts.append(f"Key skills include {top_skills}.")

    prefix = " ".join(prefix_parts)
    return (prefix + " " + summary).strip() if prefix else summary
