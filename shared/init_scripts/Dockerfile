FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

COPY shared/init_scripts/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser

COPY --from=builder /install /usr/local
COPY shared/init_scripts/ shared/init_scripts/
COPY shared/inventory.json shared/inventory.json

ENV PYTHONDONTWRITEBYTECODE=1
USER appuser

