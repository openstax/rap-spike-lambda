FROM python:3.7-alpine

# Install base packages
RUN apk add --update --no-cache --virtual .build-deps gcc g++ postgresql-dev curl \
    libffi-dev yaml-dev python3-dev py3-psutil linux-headers musl-dev && \
    apk add --no-cache --update python3 && \
    pip3 install --upgrade pip setuptools && \
    rm -rf /var/cache/apk/*

WORKDIR /app

COPY ["./requirements/main.txt", "/app"]
RUN pip install -r main.txt

COPY . .

# Set the application environment
ENV PYTHONIOENCODING utf_8
ENV PYTHONPATH /app:$PYTHONPATH
ENV PATH="/app/bin:${PATH}"
ENV FLASK_APP=/app/wsgi.py

RUN chmod +x bin/docker-entrypoint.sh
