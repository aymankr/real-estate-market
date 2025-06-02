FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY dvf-producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY immo-viz-api/immo_viz_api /app/immo_viz_api

ENV PYTHONPATH=/app

COPY dvf-producer/dvf_to_kafka.py .
RUN chmod +x dvf_to_kafka.py

ENTRYPOINT ["python", "dvf_to_kafka.py"]