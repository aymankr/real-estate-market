# property-ads-analyzer/Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer.py models.py /app/

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "/app/consumer.py"]
