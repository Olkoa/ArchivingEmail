# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# System dependencies for scientific stack, graphviz, and build tooling
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        graphviz \
        libgraphviz-dev \
        git \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for better caching
COPY requirements.txt Makefile constants.py ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Download required spaCy language models
RUN python -m spacy download fr_core_news_sm \
    && python -m spacy download de_core_news_sm

# Copy application code (limited by .dockerignore)
COPY .ragatouille ./.ragatouille
COPY app ./app
COPY data ./data
COPY src ./src
# COPY .env .env

# Ensure entrypoint script is executable
RUN chmod +x app/entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["./app/entrypoint.sh"]
