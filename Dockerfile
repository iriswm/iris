FROM docker.io/library/python:3.11-bullseye AS base

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /app
ENV PYTHONPATH="/app:/app/deps/iris_wc"
COPY deps /app/deps
COPY manage.py /app/manage.py
COPY iris /app/iris
CMD [ "/bin/sh", "-c", "./manage.py runserver 0.0.0.0:8000" ]


FROM docker.io/library/python:3.11-bullseye
RUN apt-get update && apt-get install -y gettext && rm -rf /var/lib/apt/lists/*

COPY --from=base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.dev.txt requirements.dev.txt
RUN pip3 install -r requirements.dev.txt

WORKDIR /app
ENV PYTHONPATH="/app:/app/deps/iris_wc"
CMD [ "/bin/sh", "-c", "./manage.py runserver 0.0.0.0:8000" ]
