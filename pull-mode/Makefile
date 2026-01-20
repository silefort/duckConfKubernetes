DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose

.PHONY: help build run run-multi stop restart restart-multi create_app stop_node start_node watch clean

help:
	@echo "Targets disponibles :"
	@echo "  build        - Build les images Docker"
	@echo "  run          - Lance l'API server avec 1 nœud"
	@echo "  run-multi    - Lance l'API server avec 3 nœuds"
	@echo "  stop         - Arrête tous les services"
	@echo "  restart      - Redémarre avec 1 nœud"
	@echo "  restart-multi- Redémarre avec 3 nœuds"
	@echo "  create_app   - Crée une app (ex: make create_app duckconf-1)"
	@echo "  stop_node    - Pause un nœud (ex: make stop_node app-1)"
	@echo "  start_node   - Reprend un nœud (ex: make start_node app-1)"
	@echo "  watch        - Surveille l'état des nœuds"
	@echo "  help         - Affiche cette aide"

build:
	$(DOCKER_COMPOSE) build

run:
	-$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=pull-mode") 2>/dev/null
	$(DOCKER_COMPOSE) up

run-multi:
	-$(DOCKER_COMPOSE) -f docker-compose.multi.yml down -v --remove-orphans 2>/dev/null
	-$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "name=pull-mode") 2>/dev/null
	$(DOCKER_COMPOSE) -f docker-compose.multi.yml up

stop:
	-$(DOCKER_COMPOSE) down -t 0 2>/dev/null
	-$(DOCKER_COMPOSE) -f docker-compose.multi.yml down -t 0 2>/dev/null
	@rm -f nodes/node-1_running.txt nodes/node-2_running.txt nodes/node-3_running.txt
	@rm -f api_server/desired_state.txt

restart: stop run
restart-multi: stop run-multi

create_app:
	@echo 'curl -X POST http://localhost:8081/api/apps -H "Content-Type: application/json" -d '"'"'{"name": "$(filter-out $@,$(MAKECMDGOALS))"}'"'"
	@curl -s -X POST http://localhost:8081/api/apps \
		-H "Content-Type: application/json" \
		-d '{"name": "$(filter-out $@,$(MAKECMDGOALS))"}' | python3 -m json.tool

stop_node:
	$(DOCKER) pause pull-mode_$(filter-out $@,$(MAKECMDGOALS))_1

start_node:
	$(DOCKER) unpause pull-mode_$(filter-out $@,$(MAKECMDGOALS))_1

watch:
	watch -n 1 'for f in nodes/*.txt; do echo "=== $$f ==="; cat "$$f"; echo; done'

%:
	@:
