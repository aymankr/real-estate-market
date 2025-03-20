# Immo Viz

Real estate data fetcher and visualiser.

## Getting Started

### Prerequisites

1. Copy paste the .env.example file and rename it to .env : `cp .env.example .env`

2. Make sure that the rights on .grafana_storage folder are RW for the user running the docker-compose (To be sure do `chmod 777 -R .grafana_storage`)

### Running the project

1. Run the command: `make up` or `make upd` to start the docker compose.

2. If it's your first run, launch the `make seed` command to populate the viz-db with french cities, departments and regions.

### Accessing the services

#### API

- <http://localhost:8000/>

#### Grafana

- To access the grafana server go to `localhost:3000` and login with the default credentials `user: admin` `password: admin`. When asking for a password update you can click on 'Skip'.

#### Adminer

- To access the adminer go to `localhost:8080`, select `PostgreSQL` as the system and use the following credentials: `host: immo-viz-db` `user: root, password: root`
