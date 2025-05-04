FROM python:3.12.2-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends dos2unix netcat-traditional \
 && pip install --upgrade pip setuptools \
 && pip install poetry==1.8.3 \
 && rm -rf /var/lib/apt/lists/*

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    TZ=Europe/Paris \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock poetry.toml ./
RUN poetry lock --no-update

RUN poetry install --only main --no-root

COPY . .

RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]