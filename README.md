# Immo Viz

Real estate data fetcher and visualiser.

## Getting Started - Scraper/API/Grafana

### Prerequisites

1. Copy paste the .env.example file and rename it to .env : `cp .env.example .env`

2. Make sure that the rights on .grafana_storage folder are RW for the user running the docker-compose (To be sure do `chmod 777 -R .grafana_storage`)

3. For prometheus and cAdvisor to recieve metrics from the docker daemon it is neccessary to configure docker <https://docs.docker.com/engine/daemon/prometheus/>.

### Running the project

1. Execute `docker network create immo-viz-network`

2. Execute `docker-compose up` at the project root.

This will start the fetchers, the API and the grafana server.

### Accessing the services

#### Grafana

- To access the grafana server go to `localhost:3000` and login with the default credentials `user: admin` `password: admin`. When asking for a password update you can click on 'Skip'.

#### Adminer

- To access the adminer go to `localhost:8080`, select `PostgreSQL` as the system and use the following credentials: `host: immo-viz-db` `user: root, password: root`

#### Prometheus

Analyzes resource usage from targets.

- To access go to `localhost:9090`.
- To see what targets are available `127.0.0.1:9090/targets` (to access a target's metrics from outisde the docker context, replace the host name with localhost.)

#### cAdvisor

Analyzes and exposes resource usage and performance data from running containers.

- To access go to `localhost:8083/containers`
