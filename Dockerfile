# Use an official Python base image from the Docker Hub
FROM python:3-alpine AS loopgpt-base

# Install browsers
RUN apk update && apk add --no-cache \
    firefox \
    ca-certificates

# Install utilities
RUN apk add --no-cache curl jq wget git gcc g++ libc-dev bash

# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN adduser -D -g gpt -s /bin/bash gpt

WORKDIR /app
COPY requirements.txt setup.py ./
RUN chown -R gpt:gpt . && chmod -R 755 .

USER gpt:gpt

RUN pip install --user -e .

COPY --chown=gpt:gpt . ./

ENV DISPLAY=:99 \
    PATH=/home/gpt/.local/bin:$PATH
