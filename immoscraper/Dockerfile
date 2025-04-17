FROM python:3.12.2-slim

# Install system dependencies
RUN apt-get update -y && pip install poetry==1.8.3

ARG POETRY_VERSION=1.8.3
RUN pip install "poetry==${POETRY_VERSION}"

# Configure Poetry to create a venv
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    TZ=Europe/Paris

# Copy just the configuration files to install dependencies in cache
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Install production dependencies in the venv
RUN poetry lock --no-update
RUN poetry install --no-dev --no-interaction --no-ansi

COPY . .
RUN chmod +x entrypoint.sh

# Install project dependencies
RUN poetry install --without dev

# Run the application
CMD ["/app/entrypoint.sh"]
