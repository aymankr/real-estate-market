FROM bitnami/spark:3.5.0

USER root
WORKDIR /opt/app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      kafka-python==2.0.2 \
      requests==2.31.0

COPY consumer.py models.py /opt/app/

RUN apt-get update && \
    apt-get install -y dos2unix && \
    dos2unix /opt/app/consumer.py /opt/app/models.py && \
    rm -rf /var/lib/apt/lists/*

RUN chmod +x /opt/app/consumer.py

USER 1001
