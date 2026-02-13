DOCKER ?= podman
DOCKER_COMPOSE ?= podman-compose
VERSION ?= 2

COMPOSE_FLAGS = -f version-$(VERSION)/docker-compose.yml -p version-$(VERSION)

.PHONY: help build cluster_start cluster_stop cluster_restart cluster_list app_start app_apply app_kill apps_clean apps_list node_stop node_start node_ssh api_stop api_start logs watch viddy _watch_display delete_all tmux

help:
	@echo "Commandes disponibles (VERSION=<0|1|2>):"
	@echo "  make cluster_start - Demarre le cluster"
	@echo "  make cluster_stop                        - Arrete le cluster"
	@echo "  make cluster_restart                     - Redemarre le cluster"
	@echo "  make cluster_list                        - Liste les containers d'infrastructure"
	@echo "  make app_start NAME=<name> IMAGE=<image> - Demarre un app (version-0)"
	@echo "  make app_apply NAME=<name> IMAGE=<image> - Décle un app (version-1/2)"
	@echo "  make app_kill NAME=<name>                 - Kill une app spécifique"
	@echo "  make apps_clean                          - Supprime tous les apps"
	@echo "  make apps_list                           - Liste les apps"
	@echo "  make node_stop NODE=<node>               - Pause un noeud"
	@echo "  make node_start NODE=<node>              - Unpause un noeud"
	@echo "  make node_ssh NODE=<node>                - Se connecte a un noeud"
	@echo "  make logs [SERVICE=<service>]            - Affiche les logs (tous avec couleurs ou d'un service)"
	@echo "  make api_stop                            - Pause l'api server (version-2)"
	@echo "  make api_start                           - Unpause l'api server (version-2)"
	@echo "  make watch                               - Watch l'état du cluster (version-2)"
	@echo "  make viddy                               - Watch l'état avec viddy (diff coloré)"
	@echo "  make tmux                                - Ouvre une session tmux (logs + cmds)"
	@echo "  make delete_all                          - Supprime tous les containers"

build:
	$(DOCKER_COMPOSE) $(COMPOSE_FLAGS) build

cluster_start:
	$(DOCKER_COMPOSE) $(COMPOSE_FLAGS) up

cluster_stop:
	@$(DOCKER) unpause $$($(DOCKER) ps -aq --filter status=paused) 2>/dev/null || true
	@rm -f version-$(VERSION)/.paused_*
	$(DOCKER_COMPOSE) $(COMPOSE_FLAGS) down -t 0

cluster_restart: cluster_stop cluster_start cluster_list

cluster_list:
	@echo "=============================="
	@echo "=============================="
	@echo "=============================="
	@$(DOCKER) ps -a --format "{{.Names}}\t{{.Labels.type}}" | grep -E "node|control-plane" | awk '{ print $1 }' | sort

logs:
	@RED='\033[0;31m'; \
	GREEN='\033[0;32m'; \
	YELLOW='\033[0;33m'; \
	BLUE='\033[0;34m'; \
	MAGENTA='\033[0;35m'; \
	CYAN='\033[0;36m'; \
	BRIGHT_MAGENTA='\033[1;35m'; \
	BRIGHT_CYAN='\033[1;36m'; \
	NC='\033[0m'; \
	get_color() { \
		case "$$1" in \
			app-manager) echo "$$BLUE" ;; \
			app-controller) echo "$$CYAN" ;; \
			api-server) echo "$$MAGENTA" ;; \
			node-binder) echo "$$BRIGHT_MAGENTA" ;; \
			node-controller) echo "$$BRIGHT_CYAN" ;; \
			node-1) echo "$$RED" ;; \
			node-2) echo "$$GREEN" ;; \
			node-3) echo "$$YELLOW" ;; \
			*) echo "$$NC" ;; \
		esac; \
	}; \
	colorize_logs() { \
		local service=$$1; \
		local color=$$2; \
		if $(DOCKER) ps --format '{{.Names}}' | grep -q "^version-$(VERSION)_$${service}_1$$"; then \
			$(DOCKER) logs -f --tail 20 "version-$(VERSION)_$${service}_1" 2>&1 | while IFS= read -r line; do \
				printf "%b[%s]%b %s\n" "$${color}" "$${service}" "$${NC}" "$$line"; \
			done; \
		fi; \
	}; \
	if [ -n "$(SERVICE)" ]; then \
		services=$$(echo "$(SERVICE)" | tr ',' ' '); \
		for service in $$services; do \
			color=$$(get_color "$$service"); \
			colorize_logs "$$service" "$$color" & \
		done; \
		wait; \
	else \
		colorize_logs "app-manager" "$$BLUE" & \
		colorize_logs "app-controller" "$$CYAN" & \
		colorize_logs "api-server" "$$MAGENTA" & \
		colorize_logs "node-binder" "$$BRIGHT_MAGENTA" & \
		colorize_logs "node-controller" "$$BRIGHT_CYAN" & \
		colorize_logs "node-1" "$$RED" & \
		colorize_logs "node-2" "$$GREEN" & \
		colorize_logs "node-3" "$$YELLOW" & \
		wait; \
	fi

app_start:
	@test -n "$(NAME)" || (echo "Erreur: NAME non défini. Usage: make app_start NAME=<name> IMAGE=<image>" && false)
	@test -n "$(IMAGE)" || (echo "Erreur: IMAGE non défini. Usage: make app_start NAME=<name> IMAGE=<image>" && false)
	@curl -s -X POST http://localhost:8080/app/start \
		-H "Content-Type: application/json" \
		-d '{"name": "$(NAME)", "image": "$(IMAGE)"}' | python3 -m json.tool

app_apply:
	@test -n "$(NAME)" || (echo "Erreur: NAME non défini. Usage: make app_apply NAME=<name> IMAGE=<image>" && false)
	@test -n "$(IMAGE)" || (echo "Erreur: IMAGE non défini. Usage: make app_apply NAME=<name> IMAGE=<image>" && false)
	@curl -s -X PUT http://localhost:8080/app/$(NAME) \
		-H "Content-Type: application/json" \
		-d '{"image": "$(IMAGE)"}' | python3 -m json.tool

app_kill:
	@test -n "$(NAME)" || (echo "Erreur: NAME non défini. Usage: make app_kill NAME=<name>" && false)
	@NODE=$$($(DOCKER) ps --filter "name=$(NAME)" --filter "label=type=app" --format "{{.Labels.node}}" | head -1); \
	test -n "$$NODE" || (echo "Erreur: Application $(NAME) introuvable" && false); \
	echo "make node_ssh NODE=$$NODE"; \
	echo "docker rm -f $(NAME)"
	@NODE=$$($(DOCKER) ps --filter "name=$(NAME)" --filter "label=type=app" --format "{{.Labels.node}}" | head -1); \
	$(DOCKER) exec version-$(VERSION)_$${NODE}_1 docker rm -f $(NAME) > /dev/null 2>&1

apps_clean:
	@$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "label=type=app") 2>/dev/null || true
	echo '{}' > version-$(VERSION)/apps.json
	echo '{}' > version-$(VERSION)/nodes.json

apps_list:
	@echo "APP\tNODE\tUPTIME"
	@$(DOCKER) ps --filter "label=type=app" --format "{{.Names}}\t{{.Labels.node}}\t{{.RunningFor}}"

node_stop:
	@test -n "$(NODE)" || (echo "Erreur: NODE non défini. Usage: make node_stop NODE=<node>" && false)
	@touch version-$(VERSION)/.paused_$(NODE)
	@$(DOCKER) rm -f $$($(DOCKER) ps -aq --filter "label=type=app" --filter "label=node=$(NODE)") 2>/dev/null || true
	$(DOCKER) pause version-$(VERSION)_$(NODE)_1

node_start:
	@test -n "$(NODE)" || (echo "Erreur: NODE non défini. Usage: make node_start NODE=<node>" && false)
	@rm -f version-$(VERSION)/.paused_$(NODE)
	$(DOCKER) unpause version-$(VERSION)_$(NODE)_1

node_ssh:
	@test -n "$(NODE)" || (echo "Erreur: NODE non défini. Usage: make node_ssh NODE=<node>" && false)
	@$(DOCKER) exec -it version-$(VERSION)_$(NODE)_1 /bin/bash

api_stop:
	$(DOCKER) pause version-$(VERSION)_api-server_1

api_start:
	@echo '{}' > version-$(VERSION)/nodes.json
	$(DOCKER) unpause version-$(VERSION)_api-server_1

watch:
	watch -n 2 "VERSION=$(VERSION) $(MAKE) --no-print-directory _watch_display"

viddy:
	viddy -d -n 2 "VERSION=$(VERSION) $(MAKE) --no-print-directory _watch_display"

_watch_display:
	@if [ "$(VERSION)" = "1" ] || [ "$(VERSION)" = "2" ]; then \
		echo "=== ÉTAT DÉSIRÉ (apps.json) ===" ; \
		python3 -c 'import json,os;d=json.load(open("version-$(VERSION)/apps.json")) if os.path.exists("version-$(VERSION)/apps.json") else {};[print(f"{n}: {json.dumps(i)}") for n,i in sorted(d.items())] if d else print("  (aucune app)")' ; \
		echo ; \
	fi ; \
	if [ "$(VERSION)" = "2" ]; then \
		echo "=== NOEUDS (nodes.json) ===" ; \
		python3 -c 'import json,os;d=json.load(open("version-$(VERSION)/nodes.json")) if os.path.exists("version-$(VERSION)/nodes.json") else {};print("%-20s %s"%("NOEUD","HEARTBEAT"));[print("%-20s %s"%(n,t)) for n,t in sorted(d.items())] if d else print("  (aucun heartbeat)")' ; \
		echo ; \
	fi ; \
	echo "=== APPS EN COURS ===" ; \
	for node in node-1 node-2 node-3; do \
		echo ; \
		echo "**$$node**" ; \
		apps=$$($(DOCKER) ps --filter "label=type=app" --filter "label=node=$$node" --format "  {{.Names}}\t{{.RunningFor}}"); \
		if [ -n "$$apps" ]; then \
			echo "$$apps"; \
		else \
			echo "  (aucune app)"; \
		fi; \
	done

tmux:
	@bash setup-tmux.sh $(VERSION)

delete_all:
	@$(DOCKER) unpause $$($(DOCKER) ps -aq --filter status=paused) 2>/dev/null || true
	@$(DOCKER) kill --signal KILL -a
	@$(DOCKER) rm -f $$($(DOCKER) ps -aq) 2>/dev/null || true
	@$(DOCKER) kill --signal KILL -a
	@$(DOCKER) rm -f $$($(DOCKER) ps -aq) 2>/dev/null || true
	$(DOCKER) ps -a
	

