# Variables pour supporter podman/docker
DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose

.PHONY: help build run stop clean logs shell view-running view-desired restart api-list api-add api-remove logs-api logs-scheduler logs-controller logs-node1 logs-node2 logs-node3 view-all-nodes view-nodes stop-node

help:
	@echo "Kubernetes Simulator - Commandes disponibles:"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make build         - Build les images Docker"
	@echo "  make run           - Démarre tout (API + Scheduler + Controller + 3 nœuds)"
	@echo "  make stop          - Arrête tous les services"
	@echo "  make restart       - Redémarre tous les services"
	@echo "  make stop-node NODE=node-X - Simule la perte d'un nœud"
	@echo ""
	@echo "Logs:"
	@echo "  make logs          - Affiche tous les logs"
	@echo "  make logs-api      - Logs de l'API"
	@echo "  make logs-scheduler - Logs du scheduler"
	@echo "  make logs-controller - Logs du node controller"
	@echo "  make logs-node1    - Logs du nœud 1"
	@echo "  make logs-node2    - Logs du nœud 2"
	@echo "  make logs-node3    - Logs du nœud 3"
	@echo ""
	@echo "API (gestion des containers):"
	@echo "  make api-list      - Liste les containers"
	@echo "  make api-add NAME=xxx - Ajoute un container"
	@echo "  make api-remove NAME=xxx - Supprime un container"
	@echo ""
	@echo "Monitoring:"
	@echo "  make view-nodes    - Affiche l'état des nœuds"
	@echo "  make view-all-nodes - Affiche containers sur chaque nœud"
	@echo "  make view-desired: - Affiche l'état désiré du cluster"
	@echo "  make clean         - Nettoie les fichiers générés"
	@echo ""

build:
	$(DOCKER_COMPOSE) build

run:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=duckconfkubernetes") 2>/dev/null
	$(DOCKER_COMPOSE) up

run-detached:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=duckconfkubernetes") 2>/dev/null
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down

restart: stop run

logs:
	$(DOCKER_COMPOSE) logs -f

logs-api:
	$(DOCKER_COMPOSE) logs -f api-server

logs-scheduler:
	$(DOCKER_COMPOSE) logs -f scheduler

logs-controller:
	$(DOCKER_COMPOSE) logs -f node-controller

logs-node1:
	$(DOCKER_COMPOSE) logs -f node-1

logs-node2:
	$(DOCKER_COMPOSE) logs -f node-2

logs-node3:
	$(DOCKER_COMPOSE) logs -f node-3

shell:
	$(DOCKER_COMPOSE) run --rm node-1 /bin/bash

api-list:
	@curl -s http://localhost:8080/api/containers | python3 -m json.tool

api-add:
	@curl -s -X POST http://localhost:8080/api/containers \
		-H "Content-Type: application/json" \
		-d '{"name": "$(NAME)"}' | python3 -m json.tool

api-remove:
	@curl -s -X DELETE http://localhost:8080/api/containers/$(NAME) | python3 -m json.tool

view-nodes:
	@curl -s http://localhost:8080/api/nodes | python3 -m json.tool

stop-node:
	@echo "Arrêt du nœud $(NODE)..."
	$(DOCKER_COMPOSE) stop $(NODE)
	@echo "✓ Nœud $(NODE) arrêté - Le node controller devrait détecter la perte"

view-all-nodes:
	@for node in 1 2 3; do \
		echo "=== NODE-$$node ==="; \
		echo "Désiré:"; \
		if [ -f nodes/node-$${node}_desired.txt ]; then cat nodes/node-$${node}_desired.txt; else echo "  Aucun"; fi; \
	echo "\nRunning:"; \
		if [ -f nodes/node-$${node}_running.txt ]; then cat nodes/node-$${node}_running.txt; else echo "  Aucun"; fi; \
		echo ""; \
	done

view-desired:
	@echo "État désiré :"
	@if [ -f desired_state.txt ]; then cat desired_state.txt; else echo "Aucun"; fi

clean:
	rm -f nodes/node-1_desired.txt nodes/node-1_running.txt
	rm -f nodes/node-2_desired.txt nodes/node-2_running.txt
	rm -f nodes/node-3_desired.txt node-3_running.txt
	rm -f desired_state.txt
	@echo "✓ Fichiers de state nettoyés"

clean-all: clean stop
	$(DOCKER_COMPOSE) down --rmi all --volumes
	@echo "✓ Images Docker et volumes supprimés"
