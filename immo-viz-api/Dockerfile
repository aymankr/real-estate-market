FROM python:3.12.2-slim

RUN apt-get update -y \
 && apt-get install -y libpq-dev gcc \
 && pip install poetry==1.8.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN poetry lock --no-update

RUN poetry install --without dev

COPY . .

CMD ["poetry", "run", "uvicorn", "immo_viz_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
