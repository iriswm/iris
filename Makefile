.PHONY: makemessages
makemessages:
	@$(exec) django-admin makemessages -l es --no-obsolete --no-location
.PHONY: compilemessages
compilemessages:
	@$(exec) django-admin compilemessages -l es
.PHONY: style
style:
	@$(exec) isort manage.py iris deps/iris_wc
	@$(exec) black manage.py iris deps/iris_wc
.PHONY: db-up
db-up:
	@$(exec) podman run --rm -d --name iris_db -p 15432:5432 \
		-v ./state/pg_data:/var/lib/postgresql/data \
		-e POSTGRES_DB=iris \
		-e POSTGRES_USER=iris \
		-e POSTGRES_PASSWORD=iris \
		docker.io/library/postgres:15.1-alpine3.16
.PHONY: db-down
db-down:
	@$(exec) podman stop iris_db
