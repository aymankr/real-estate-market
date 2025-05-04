#!/usr/bin/env bash
set -euo pipefail

sleep 5

# -- wait for Kafka --
echo "[entrypoint] waiting for Kafka at ${KAFKA_HOST}…"
host="${KAFKA_HOST%%:*}" port="${KAFKA_HOST##*:}"
for i in $(seq 1 20); do
  if nc -z "$host" "$port"; then
    echo "[entrypoint] Kafka is up!"
    break
  fi
  echo "[entrypoint] Kafka not ready (attempt $i/20), sleeping 3s"
  sleep 3
done

INTERVAL="${START_SCHEDULER_INTERVAL}"
echo "[entrypoint] will run scheduler every ${INTERVAL}s"

while true; do
  echo "[entrypoint] $(date '+%F %T') — running analysis_scheduler"
  if poetry run python -m analysis_scheduler; then
    echo "[entrypoint] scheduler finished successfully"
  else
    echo "[entrypoint] scheduler errored, will retry in ${INTERVAL}s"
  fi
  sleep "${INTERVAL}"
done
