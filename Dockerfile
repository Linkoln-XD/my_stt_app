# syntax=docker/dockerfile:1
# CPU image for local Docker checks. The NVIDIA server uses Dockerfile.gpu.

FROM node:20-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund 2>/dev/null || npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/app/data \
    STATIC_DIR=/app/static \
    PORT=8080 \
    HF_HOME=/root/.cache/huggingface

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY backend/requirements-docker.txt ./
RUN pip install --upgrade pip \
    && pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements-docker.txt \
    && python -c "import torch; v=torch.__version__.split('+')[0]; assert v=='2.8.0', torch.__version__; assert not torch.version.cuda, torch.version.cuda"

COPY backend/ ./
COPY --from=frontend-build /build/frontend/dist /app/static

COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN mkdir -p /app/data/uploads /app/data/processed

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health')" || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
