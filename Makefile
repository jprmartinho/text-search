.PHONY: help build up down down-volumes rmi-dangling show-logs-es show-logs-api tail-logs-api setup-dev pre-commit-auto run-tests

VENV = .venv
COMPOSE_FILE = dev.yml

help:
	@echo "Available targets:"
	@echo "  build              Build and start the Docker containers"
	@echo "  up                 Start the Docker containers"
	@echo "  down               Stop the Docker containers"
	@echo "  down-volumes       Stop the Docker containers and remove volumes"
	@echo "  rmi-dangling       Remove dangling docker images"
	@echo "  show-logs-es       Show logs for the Elasticsearch service"
	@echo "  show-logs-api      Show logs for the Flask API service"
	@echo "  tail-logs-api      Tail logs for the Flask API service"
	@echo "  setup-dev          Setup both dev venv and requirements"
	@echo "  pre-commit-auto    Update pre-commit and run for all files"
	@echo "  update-reqs-dev    Update requirements for dev"
	@echo "  run-tests          Run tests and coverage"
	@echo "  clean-dev          Clean dev env"


build:
	docker compose -f $(COMPOSE_FILE) up --build -d --remove-orphans

up:
	docker compose -f $(COMPOSE_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) down

down-volumes:
	docker compose -f $(COMPOSE_FILE) down -v

rmi-dangling:
	docker images --filter "dangling=true" -q | xargs docker rmi

show-logs-es:
	docker compose -f $(COMPOSE_FILE) logs es

show-logs-api:
	docker compose -f $(COMPOSE_FILE) logs api

tail-logs-api:
	docker compose -f $(COMPOSE_FILE) logs -f api

flask-regenerate-index:
	docker compose -f $(COMPOSE_FILE) exec api flask regenerateindex

flask-get-mapping:
	docker compose -f $(COMPOSE_FILE) exec api flask getmapping

reload-wiki-pages:
	docker compose -f $(COMPOSE_FILE) exec api python load_wiki_pages.py

setup-dev:
	python -m venv $(VENV) \
	&& . $(VENV)/bin/activate \
	&& python -m pip install -qqq -r ./requirements/dev.txt \
	&& pre-commit install

pre-commit-auto:
	pre-commit autoupdate
	pre-commit run --all-files

update-reqs-dev:
	python -m piptools compile -o ./requirements/dev.txt ./requirements/dev.in

run-tests:
	python -m coverage erase
	python -m coverage run -m pytest -vvv
	python -m coverage report
	python -m coverage html
	@echo "Run 'python -m http.server 5000' to view 'htmlcov'"

clean-dev:
	rm -rf .*/__pycache__ .mypy_cache .pytest_cache .coverage htmlcov .venv
