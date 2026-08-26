FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Clone aider repo for benchmark scripts & Exercism exercises
RUN git clone --depth 1 https://github.com/Aider-AI/aider.git /opt/aider

RUN pip install --no-cache-dir \
    -e /opt/aider[dev] \
    pytest \
    pandas \
    matplotlib \
    tabulate \
    scipy \
    lox \
    imgcat

WORKDIR /opt/aider/benchmark
RUN ./clone-exercism.sh
ENV AIDER_DOCKER=1

# Wrapper entrypoint that logs traces and runs the benchmark
COPY ./containers/aider-entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
