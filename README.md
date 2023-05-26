# iris
Workshop oriented task manager.
## Development
### Requirements
* podman
* podman-compose
* make
### Bootstrap a new dev server
Create a `.env` file in the project root with the next contents:
```
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=django-insecure-gs=xloqs7ztt*v)e_w=!moh+_vvfu25#_$c^yhdspv_wosx&om
POSTGRES_DB=iris
POSTGRES_USER=iris
POSTGRES_PASSWORD=iris
```
Run the next commands:
```
make up
make migrate
make init-db
make init-db-dev  # To install the test data
make compilemessages
podman-compose restart webapp
```
Check the `init-db-dev` test data structure in [docs/testdata.md](docs/testdata.md).
