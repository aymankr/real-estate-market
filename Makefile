default: help

.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

up: docker-compose.yml .env		# Launch the docker compose
	echo "Starting the server..."
	docker compose up

upd: docker-compose.yml .env	# Launch the docker compose in detached mode
	echo "Starting the server..."
	docker compose up -d

down: docker-compose.yml .env	# Stop the docker compose
	echo "Stopping the server..."
	docker compose down

re: docker-compose.yml .env 	# Restart the docker compose
	echo "Restarting the server..."
	docker compose down && docker compose up

red: docker-compose.yml .env	# Restart the docker compose in detached mode
	echo "Restarting the server..."
	docker compose down && docker compose up -d

logs: docker-compose.yml .env	# Show the logs of the docker compose
	docker compose logs -f

seed: docker-compose.yml .env	# Seed the database
	echo "Seeding the database..."
	docker exec -it t-dat-902-bdx_8-immo-viz-api-1 poetry run python -m immo_viz_api.seeder
	echo "Seeding done."
