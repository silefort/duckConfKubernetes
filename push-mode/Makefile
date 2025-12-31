# Variables pour supporter podman/docker
DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose

.PHONY: help build run stop clean logs restart start-container get-containers view-nodes logs-api logs-node1 logs-node2 logs-node3

help:
	@echo "Kubernetes Simulator - Push Mode"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make build         - Build les images Docker"
	@echo "  make run           - Démarre l'API server + 3 nœuds"
	@echo "  make stop          - Arrête tous les services"
	@echo "  make restart       - Redémarre tous les services"
	@echo ""
	@echo "Logs:"
	@echo "  make logs          - Affiche tous les logs"
	@echo "  make logs-api      - Logs de l'API"
	@echo "  make logs-node1    - Logs du nœud 1"
	@echo "  make logs-node2    - Logs du nœud 2"
	@echo "  make logs-node3    - Logs du nœud 3"
	@echo ""
	@echo "API (gestion des containers):"
	@echo "  make start-container NAME=xxx - Démarre un container (auto-schedulé)"
	@echo "  make get-containers - Liste tous les containers du cluster"
	@echo ""
	@echo "Monitoring:"
	@echo "  make view-nodes    - Affiche les containers sur chaque nœud"
	@echo "  make clean         - Nettoie les fichiers générés"
	@echo ""

build:
	$(DOCKER_COMPOSE) build

run:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=push-mode") 2>/dev/null
	$(DOCKER_COMPOSE) up

run-detached:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=push-mode") 2>/dev/null
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down

restart: stop run

logs:
	$(DOCKER_COMPOSE) logs -f

logs-api:
	$(DOCKER_COMPOSE) logs -f api-server

logs-node1:
	$(DOCKER_COMPOSE) logs -f node-1

logs-node2:
	$(DOCKER_COMPOSE) logs -f node-2

logs-node3:
	$(DOCKER_COMPOSE) logs -f node-3

start-container:
	@curl -s -X POST http://localhost:8080/container/start \
		-H "Content-Type: application/json" \
		-d '{"name": "$(NAME)"}' | python3 -m json.tool

get-containers:
	@curl -s http://localhost:8080/containers | python3 -m json.tool

view-nodes:
	@for node in 1 2 3; do \
		echo "=== NODE-$$node ==="; \
		if [ -f nodes/node-$${node}_running.txt ]; then cat nodes/node-$${node}_running.txt; else echo "  Aucun"; fi \
	done

clean:
	rm -f node-1_running.txt
	rm -f node-2_running.txt
	rm -f node-3_running.txt
	@echo "✓ Fichiers de state nettoyés"

clean-all: clean stop
	$(DOCKER_COMPOSE) down --rmi all --volumes
	@echo "✓ Images Docker et volumes supprimés"
