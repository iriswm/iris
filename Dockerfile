FROM docker.io/library/python:3.9-bullseye
RUN apt-get update && apt-get install -y gettext && rm -rf /var/lib/apt/lists/*
WORKDIR /app
VOLUME /app/state
ENV PYTHONPATH="/app:/app/deps/iris_wc"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY deps /app/deps
COPY manage.py /app/manage.py
COPY iris /app/iris
CMD [ "/bin/sh", "-c", "./manage.py migrate; ./manage.py compilemessages -l es; ./manage.py loaddata iris_auth_groups iris_dev_users; ./manage.py runserver 0.0.0.0:8000" ]
