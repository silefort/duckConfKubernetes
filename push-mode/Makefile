# Variables pour supporter podman/docker
DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose

.PHONY: help build run run-multi stop restart restart-multi start_app stop_node start_node watch

help:
	@echo "Kubernetes Simulator - Push Mode"
	@echo ""
	@echo "  make build              - Build les images"
	@echo "  make run-mono           - Demarre avec 1 noeud"
	@echo "  make run                - Demarre avec 3 noeuds"
	@echo "  make stop               - Arrete tous les services"
	@echo "  make restart-mono       - Redemarre tous les services"
	@echo "  make restart            - Redemarre tous les services avec 3 noeuds"
	@echo "  make start_app <app>    - Demarre une app sur un noeud"
	@echo "  make stop_node <node>   - Arrete un noeud"
	@echo "  make start_node <node>  - Demarre un noeud"
	@echo "  make watch              - Surveille les apps sur chaque noeud"
	@echo ""

build:
	$(DOCKER_COMPOSE) build

run-mono:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=push-mode") 2>/dev/null
	@touch nodes/node-1_running.txt
	$(DOCKER_COMPOSE) up

run:
	-$(DOCKER_COMPOSE) -f docker-compose.multi.yml down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=push-mode") 2>/dev/null
	@touch nodes/node-1_running.txt nodes/node-2_running.txt nodes/node-3_running.txt
	$(DOCKER_COMPOSE) -f docker-compose.multi.yml up

stop:
	-$(DOCKER_COMPOSE) down -t 0 2>/dev/null
	-$(DOCKER_COMPOSE) -f docker-compose.multi.yml down -t 0 2>/dev/null
	@rm -f nodes/node-1_running.txt nodes/node-2_running.txt nodes/node-3_running.txt

restart-mono: stop run-mono
restart: stop run

start_app:
	@echo 'curl -X POST http://localhost:8080/app/start -H "Content-Type: application/json" -d '"'"'{"name": "$(filter-out $@,$(MAKECMDGOALS))"}'"'"''
	@curl -s -X POST http://localhost:8080/app/start \
		-H "Content-Type: application/json" \
		-d '{"name": "$(filter-out $@,$(MAKECMDGOALS))"}' | python3 -m json.tool

stop_node:
	@cp nodes/$(filter-out $@,$(MAKECMDGOALS))_running.txt nodes/$(filter-out $@,$(MAKECMDGOALS))_running.txt.paused 2>/dev/null || true
	@echo "" > nodes/$(filter-out $@,$(MAKECMDGOALS))_running.txt
	$(DOCKER) pause pull-mode_$(filter-out $@,$(MAKECMDGOALS))_1

start_node:
	mv nodes/$(filter-out $@,$(MAKECMDGOALS))_running.txt.paused nodes/$(filter-out $@,$(MAKECMDGOALS))_running.txt 2>/dev/null || true
	@rm -f nodes/$(filter-out $@,$(MAKECMDGOALS))_running.txt.paused
	$(DOCKER) unpause pull-mode_$(filter-out $@,$(MAKECMDGOALS))_1

watch:
	watch -n 1 'for f in nodes/*.txt; do echo "=== $$f ==="; cat "$$f"; echo; done'

%:
	@:
