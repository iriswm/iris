COMPOSE_CMD := podman-compose

.PHONY: build
build:
	@$(exec) $(COMPOSE_CMD) build
.PHONY: up
up:
	@$(exec) $(COMPOSE_CMD) up -d
.PHONY: down
down:
	@$(exec) $(COMPOSE_CMD) down

COMPOSE_EXEC_CMD := $(COMPOSE_CMD) exec webapp

.PHONY: cmd
cmd:
	@$(exec) echo $(COMPOSE_EXEC_CMD)

.PHONY: migrate
migrate:
	@$(exec) $(COMPOSE_EXEC_CMD) ./manage.py migrate
.PHONY: makemigrations
makemigrations:
	@$(exec) $(COMPOSE_EXEC_CMD) ./manage.py makemigrations
.PHONY: makemessages
makemessages:
	@$(exec) $(COMPOSE_EXEC_CMD) django-admin makemessages -l es --no-obsolete --no-location
.PHONY: compilemessages
compilemessages:
	@$(exec) $(COMPOSE_EXEC_CMD) django-admin compilemessages -l es

.PHONY: style
style:
	@$(exec) $(COMPOSE_EXEC_CMD) isort manage.py iris deps/iris_wc
	@$(exec) $(COMPOSE_EXEC_CMD) black manage.py iris deps/iris_wc

.PHONY: style-check
style-check:
	@$(exec) $(COMPOSE_EXEC_CMD) isort --check manage.py iris deps/iris_wc
	@$(exec) $(COMPOSE_EXEC_CMD) black --check manage.py iris deps/iris_wc
