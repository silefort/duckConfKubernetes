# Variables pour supporter podman/docker
DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose

.PHONY: help build run stop restart stop_node start_node start_app list_apps clean_apps ps kill_app ssh

help:
	@echo "Kubernetes Simulator - Push Mode"
	@echo ""
	@echo "  make run                          - Demarre le cluster"
	@echo "  make stop                         - Arrete le cluster"
	@echo "  make restart                      - Redemarre le cluster"
	@echo "  make logs                         - Affiche les logs des containers"
	@echo ""
	@echo "  make start_app <image>      			 - Demarre un app"
	@echo "  make clean_apps             			 - Supprime tous les apps"
	@echo "  make ps                           - Liste les apps (via podman)"
	@echo ""
	@echo "  make stop_node <node>             - Pause un noeud"
	@echo "  make start_node <node>            - Unpause un noeud"
	@echo "  make ssh <node>                   - Se connecte a un noeud"
	@echo ""
	@echo "  make kill_app node=<NODE> app=<NAME>"
	@echo "    Ex: make kill_app node=node-1 app=app-1"
	@echo "    (Utilisez 'make ps' pour voir les valeurs NODE et NAME)"
	@echo ""

build:
	$(DOCKER_COMPOSE) build

run:
	-$(DOCKER_COMPOSE) down -t 0 -v --remove-orphans 2>/dev/null
	$(DOCKER_COMPOSE) up

stop:
	-$(DOCKER) ps -a --filter "status=paused" -q | xargs -r $(DOCKER) unpause 2>/dev/null
	-$(DOCKER_COMPOSE) down -t 0 -v --remove-orphans 2>/dev/null
	-$(DOCKER) ps -aq --filter "name=duckconf-" | xargs -r $(DOCKER) rm -f 2>/dev/null || true
	-$(DOCKER) ps -aq --filter "name=push-mode" | xargs -r $(DOCKER) rm -f 2>/dev/null || true

restart: stop run

logs:
	$(DOCKER_COMPOSE) logs -f

start_app:
	@curl -s -X POST http://localhost:8080/app/start \
		-H "Content-Type: application/json" \
		-d '{"image": "$(filter-out $@,$(MAKECMDGOALS))"}' | python3 -m json.tool

clean_apps:
	@$(DOCKER) ps -aq --filter "name=duckconf-" | xargs -r $(DOCKER) rm -f 2>/dev/null || true

ps:
	@printf "%-15s %-15s %s\n" "NAME" "NODE" "STATUS"
	@$(DOCKER) ps --filter "name=duckconf-" --format "{{.Names}}\t{{.Status}}" | \
		sed 's/duckconf-\(node-[0-9]\)-/\1\t/' | \
		awk -F'\t' '{printf "%-15s %-15s %s\n", $$2, $$1, $$3}'

stop_node:
	@echo "Arrêt des apps sur $(filter-out $@,$(MAKECMDGOALS))..."
	@$(DOCKER) ps -q --filter "label=node=$(filter-out $@,$(MAKECMDGOALS))" | xargs -r $(DOCKER) stop
	@echo "Pause du nœud $(filter-out $@,$(MAKECMDGOALS))..."
	@$(DOCKER) pause push-mode_$(filter-out $@,$(MAKECMDGOALS))_1

start_node:
	@echo "Redémarrage du nœud $(filter-out $@,$(MAKECMDGOALS))..."
	@$(DOCKER) unpause push-mode_$(filter-out $@,$(MAKECMDGOALS))_1
	@echo "Redémarrage des apps sur $(filter-out $@,$(MAKECMDGOALS))..."
	@$(DOCKER) ps -a -q --filter "label=node=$(filter-out $@,$(MAKECMDGOALS))" --filter "status=exited" | xargs -r $(DOCKER) start

ssh:
	@$(DOCKER) exec -it push-mode_$(filter-out $@,$(MAKECMDGOALS))_1 /bin/bash

kill_app:
	@podman exec -it push-mode_$(node)_1 docker rm -f duckconf-$(node)-$(app)

%:
	@:
