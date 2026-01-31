# Variables pour supporter podman/docker
DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose

.PHONY: help build run stop restart stop_node start_node start_container list_containers stop_container clean_containers ps

help:
	@echo "Kubernetes Simulator - Push Mode"
	@echo ""
	@echo "  make build                        - Build les images"
	@echo "  make run                          - Demarre le cluster (3 noeuds)"
	@echo "  make stop                         - Arrete le cluster"
	@echo "  make restart                      - Redemarre le cluster"
	@echo "  make stop_node <node>             - Arrete un noeud"
	@echo "  make start_node <node>            - Demarre un noeud"
	@echo ""
	@echo "Containers:"
	@echo "  make start_container <image>      - Demarre un container (via API)"
	@echo "  make list_containers              - Liste les containers (via API)"
	@echo "  make stop_container <name>        - Arrete un container (via API)"
	@echo "  make clean_containers             - Supprime tous les containers duckconf-*"
	@echo "  make ps                           - Liste les containers duckconf-* (via podman)"
	@echo ""

build:
	$(DOCKER_COMPOSE) build

run:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=push-mode") 2>/dev/null
	$(DOCKER_COMPOSE) up

stop:
	-$(DOCKER_COMPOSE) down -t 0 2>/dev/null

restart: stop run

stop_node:
	$(DOCKER) pause push-mode_$(filter-out $@,$(MAKECMDGOALS))_1

start_node:
	$(DOCKER) unpause push-mode_$(filter-out $@,$(MAKECMDGOALS))_1

# Containers (via API server)
start_container:
	@curl -s -X POST http://localhost:8080/container/start \
		-H "Content-Type: application/json" \
		-d '{"image": "$(filter-out $@,$(MAKECMDGOALS))"}' | python3 -m json.tool

list_containers:
	@curl -s http://localhost:8080/container/list | python3 -m json.tool

stop_container:
	@curl -s -X POST http://localhost:8080/container/stop \
		-H "Content-Type: application/json" \
		-d '{"name": "$(filter-out $@,$(MAKECMDGOALS))"}' | python3 -m json.tool

clean_containers:
	@for node in node-1 node-2 node-3; do \
		$(DOCKER) exec push-mode_$${node}_1 sh -c 'docker ps -aq --filter "name=duckconf-" | xargs -r docker rm -f' 2>/dev/null || true; \
	done

ps:
	@$(DOCKER) ps --filter "name=duckconf-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

%:
	@:
