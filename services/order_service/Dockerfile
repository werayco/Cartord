    FROM python:3.12-slim AS builder

    WORKDIR /app

    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        librdkafka-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

    COPY requirements.txt .
    RUN pip install --no-cache-dir --user -r requirements.txt --timeout=9000


    FROM python:3.12-slim

    WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        librdkafka1 \
        && rm -rf /var/lib/apt/lists/*

    RUN groupadd -r appuser && useradd -r -g appuser appuser

    COPY --from=builder /root/.local /home/appuser/.local
    COPY . .

    RUN chown -R appuser:appuser /app /home/appuser/.local
    USER appuser

    ENV PATH=/home/appuser/.local/bin:$PATH

    EXPOSE 9006

    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9006", "--reload"]