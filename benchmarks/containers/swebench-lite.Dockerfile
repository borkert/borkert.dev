FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    swebench \
    datasets \
    openai \
    rich \
    tenacity

WORKDIR /workspace

COPY ./containers/swebench-lite-entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
