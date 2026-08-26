FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    git+https://github.com/sierra-research/tau-bench.git \
    openai \
    litellm \
    rich \
    tenacity \
    pydantic \
    datasets

WORKDIR /workspace

COPY ./containers/taubench-entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
