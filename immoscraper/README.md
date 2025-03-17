# immoscraper

Immo data scraper tool.

## Installation

### Requirements

- Python 3.12.2 or pyenv or asdf (asdf recommanded)
- Poetry

### Installation steps

Inside the root `immoscraper` directory, launch the command:

```bash
poetry install
```

## How to launch a scrap

### Locally (pap.fr example)

Inside the root `immoscraper` directory, launch the command:

```bash
poetry run scrapy crawl pap
```

### Using docker

Inside the root `immoscraper` directory, launch the command:

```bash
docker build -t immoscraper .
docker run -tdi immoscraper
```
