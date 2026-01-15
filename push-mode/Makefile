# Variables pour supporter podman/docker
DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose

.PHONY: help build run stop restart start

help:
	@echo "Kubernetes Simulator - Push Mode"
	@echo ""
	@echo "  make build              - Build les images"
	@echo "  make run                - Demarre l'API server + 3 noeuds"
	@echo "  make stop               - Arrete tous les services"
	@echo "  make restart            - Redemarre tous les services"
	@echo "  make start <app>        - Demarre une app (auto-schedule)"
	@echo ""

build:
	$(DOCKER_COMPOSE) build

run:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=push-mode") 2>/dev/null
	$(DOCKER_COMPOSE) up

stop:
	$(DOCKER_COMPOSE) down

restart: stop run

start:
	@echo 'curl -X POST http://localhost:8080/app/start -H "Content-Type: application/json" -d '"'"'{"name": "$(filter-out $@,$(MAKECMDGOALS))"}'"'"''
	@curl -s -X POST http://localhost:8080/app/start \
		-H "Content-Type: application/json" \
		-d '{"name": "$(filter-out $@,$(MAKECMDGOALS))"}' | python3 -m json.tool

%:
	@:
