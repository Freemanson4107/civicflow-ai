# CivicFlow AI backend — Docker build for Render.
#
# WHY DOCKER INSTEAD OF RENDER'S NATIVE PYTHON RUNTIME:
# The document-scan feature uses pytesseract, which is only a Python wrapper
# around the `tesseract` command-line OCR engine. `pip install -r
# requirements.txt` installs the wrapper but NOT the underlying engine.
# Render's native Python runtime has no mechanism to install system
# (apt) packages, so tesseract would be missing in production and
# POST /api/documents/scan would fail with a 500 even though it works
# locally (where tesseract-ocr is already on your machine/this sandbox).
# Docker lets us apt-get install the real binary so prod matches local.

FROM python:3.12-slim

# tesseract-ocr: the actual OCR engine binary (pytesseract just calls this)
# tesseract-ocr-eng: English language data (default install includes it on
#   most distros, but pinned explicitly here so it's never silently missing)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injects $PORT at runtime; 10000 is just a sane local default.
EXPOSE 10000
ENV PORT=10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
