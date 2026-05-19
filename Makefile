.PHONY: run stop destroy logs

SERVICES := postgres redis back admin ray
COMPOSE_FILES := -f docker-compose.yaml -f docker-compose.vars.yaml

run:
	docker compose $(COMPOSE_FILES) up -d $(SERVICES) --build --force-recreate

stop:
	docker compose $(COMPOSE_FILES) stop $(SERVICES)

restart: stop run

destroy:
	docker compose $(COMPOSE_FILES) down --volumes

logs:
	docker compose $(COMPOSE_FILES) logs -f

dev_stack:
	docker compose $(COMPOSE_FILES) -f docker-compose.yaml -f docker-compose.vars.yaml -f docker-compose.dev-network.yaml up postgres redis
