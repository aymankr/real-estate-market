FROM python:3.12.2-slim

# Install system dependencies
RUN apt-get update -y
RUN pip install poetry==1.8.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Prepare project files
WORKDIR /app
COPY . .

# Install project dependencies
RUN poetry install --without dev

# Run the application
CMD [ "poetry", "run", "python", "-m", "analysis_scheduler" ]