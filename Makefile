.PHONY: help build up down down-volumes rmi-dangling show-logs-es show-logs-api tail-logs-api init-deps

VENV = .venv
COMPOSE_FILE = local.yml

help: ## Display this help message
	@echo "Available targets:"
	@echo "  build            Build and start the Docker containers"
	@echo "  up               Start the Docker containers"
	@echo "  down             Stop the Docker containers"
	@echo "  down-volumes     Stop the Docker containers and remove volumes"
	@echo "  rmi-dangling     Remove dangling docker images"
	@echo "  show-logs-es     Show logs for the Elasticsearch service"
	@echo "  show-logs-api    Show logs for the Flask API service"
	@echo "  tail-logs-api    Tail logs for the Flask API service"
	@echo "  init-deps        Initialize venv and dependencies"


build: ## Build and start the Docker containers
	docker compose -f $(COMPOSE_FILE) up --build -d --remove-orphans

up: ## Start the Docker containers
	docker compose -f $(COMPOSE_FILE) up -d

down: ## Stop the Docker containers
	docker compose -f $(COMPOSE_FILE) down

down-volumes: ## Stop the Docker containers and remove volumes
	docker compose -f $(COMPOSE_FILE) down -v

rmi-dangling: ## Remove dangling docker images
	docker images --filter "dangling=true" -q | xargs docker rmi

show-logs-es: ## Show logs for the es service
	docker compose -f $(COMPOSE_FILE) logs es

show-logs-api: ## Show logs for the api service
	docker compose -f $(COMPOSE_FILE) logs api

tail-logs-api: ## Tail logs for the api service
	docker compose -f $(COMPOSE_FILE) logs -f api

init-deps: ## Initialize venv and dependencies
	python -m venv $(VENV) && . $(VENV)/bin/activate
	python -m pip install pip-tools
	python -m piptools compile -o ./requirements/local.txt local.in
	python -m pip check

pre-commit:
	pre-commit install
	pre-commit autoupdate
	pre-commit run --all-files
