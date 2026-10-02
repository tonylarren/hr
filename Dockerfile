FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PADDLE_PDX_CACHE_HOME=/opt/paddlex \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

# OpenCV / Paddle runtime libs
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

# Bake the OCR models into the image so the container starts fast and works offline.
ARG OCR_LANG=en
ENV OCR_LANG=${OCR_LANG}
COPY app/ocr.py /tmp/warm/ocr.py
RUN cd /tmp/warm && python -c "from ocr import build_engine; build_engine('${OCR_LANG}')" \
    && rm -rf /tmp/warm

COPY app ./app

# /data holds the OAuth sign-in token (persisted in a named volume).
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data \
    && chown -R appuser /srv /opt/paddlex /data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Single worker: each worker loads its own copy of the models and OCR is serialized anyway.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
