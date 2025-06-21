FROM bitnami/spark:3.5.0

USER root
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-pip python3-dev gcc && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/spark/.ivy2 && chown -R 1001:1001 /home/spark

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY consumer.py models.py ./

USER 1001
ENV HOME=/home/spark \
    PYTHONPATH=/app \
    SPARK_IVY_DIR=/home/spark/.ivy2

CMD spark-submit \
    --master ${SPARK_MASTER_URL:-spark://spark-master:7077} \
    --deploy-mode client \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
    --conf spark.jars.ivy=${SPARK_IVY_DIR} \
    --conf spark.hadoop.hadoop.security.authentication=simple \
    --conf spark.hadoop.hadoop.security.authorization=false \
    consumer.py
