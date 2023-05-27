FROM docker.io/library/python:3.11-bullseye AS dev
RUN apt-get update && apt-get install -y gettext && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY requirements.dev.txt requirements.dev.txt
RUN pip3 install -r requirements.dev.txt

COPY deps /app/deps
COPY manage.py /app/manage.py
COPY iris /app/iris
WORKDIR /app
ENV PYTHONPATH="/app:/app/deps/iris_wc"
RUN ./manage.py compilemessages


FROM docker.io/library/python:3.11-bullseye

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY --from=dev /app /app
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/deps/iris_wc"
CMD [ "./manage.py runserver 0.0.0.0:8000" ]
