# iris
Workshop oriented task manager.
## Development
### Requirements
* podman
* podman-compose
* make
### Bootstrap a new dev server
```
make up
make migrate
make init-db
make init-db-dev
make compilemessages
podman-compose restart webapp
```
