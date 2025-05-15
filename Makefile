# Number of Spark replicas (fallback to .env or default to 2)
WORKERS ?= $(SPARK_WORKER_REPLICAS)
WORKERS := $(or $(WORKERS),2)

default: help

.PHONY: help build up upd down re red logs seed scale clean

help: # Displays the help for the Makefile recipes
	@grep -E '^[a-zA-Z0-9 -]+:.*#' Makefile | sort | \
	while read -r l; do \
	  printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; \
	done

build: docker-compose.yml .env # Builds all Docker images
	@echo "→ docker compose build"
	docker compose build

up: docker-compose.yml .env build # Starts the stack (attached), rebuilds if necessary, scales spark-worker
	@echo "→ docker compose up --build (workers=$(WORKERS))"
	docker compose up --build --remove-orphans --scale spark-worker=$(WORKERS)

upd: docker-compose.yml .env build # Starts in detached mode, rebuilds if necessary, scales spark-worker
	@echo "→ docker compose up -d --build (workers=$(WORKERS))"
	docker compose up -d --build --remove-orphans --scale spark-worker=$(WORKERS)

down: docker-compose.yml .env # Stops and removes orphan containers
	@echo "→ docker compose down --remove-orphans"
	docker compose down --remove-orphans

re:                            # Restarts the stack (attached)
	@$(MAKE) down
	@$(MAKE) up

red:                           # Restarts in detached mode
	@$(MAKE) down
	@$(MAKE) upd

logs: docker-compose.yml .env  # Displays logs in real-time
	@echo "→ docker compose logs -f"
	docker compose logs -f

seed: docker-compose.yml .env  # Seeds the immo-viz-api database
	@echo "→ Seeding the database..."
	docker exec -it $$(docker compose ps -q immo-viz-api) \
	  poetry run python -m immo_viz_api.seeder
	@echo "→ Seeding done."

scale: docker-compose.yml .env # Scales only spark-worker
	@echo "→ Scaling spark-worker to $(WORKERS)"
	docker compose up -d --no-deps --scale spark-worker=$(WORKERS) spark-worker

clean: docker-compose.yml .env # Stops everything and removes volumes + orphans
	@echo "→ docker compose down --volumes --remove-orphans"
	docker compose down --volumes --remove-orphans
