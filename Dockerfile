FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

CMD exec python -m uvicorn dhoni_instagram_agent.api.app:app --host 0.0.0.0 --port ${PORT}