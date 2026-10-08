FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Model downloads come from external hosts (GitHub releases, NLTK) that can
# time out, so they live in their own layer with retries: a failed download
# never invalidates the pip layer, and a re-run only re-attempts this step.
RUN ok=0; \
    for i in 1 2 3 4 5; do \
        python -m spacy download en_core_web_sm && ok=1 && break || sleep 10; \
    done; \
    [ "$ok" = 1 ] || exit 1; \
    for i in 1 2 3 4 5; do \
        python -m nltk.downloader punkt punkt_tab stopwords wordnet omw-1.4 && ok=2 && break || sleep 10; \
    done; \
    [ "$ok" = 2 ] || exit 1; \
    python -c "import spacy; spacy.load('en_core_web_sm')"

COPY . .

RUN mkdir -p uploads outputs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
