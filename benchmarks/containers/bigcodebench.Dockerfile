FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --default-timeout=1000 --retries 5 --no-cache-dir \
    bigcodebench \
    numpy \
    pandas \
    scipy \
    requests \
    matplotlib \
    rich \
    tenacity && \
    python3 -c 'p="/usr/local/lib/python3.10/site-packages/bigcodebench/sanitize.py"; c=open(p).read(); open(p,"w").write(c.replace("def code_extract(text: str) -> str:\n", "def code_extract(text: str) -> str:\n    if not text: return \"\"\n"))' && \
    python3 -c 'p="/usr/local/lib/python3.10/site-packages/bigcodebench/provider/openai.py"; c=open(p).read(); open(p,"w").write(c.replace("for item in ret.choices:\n                outputs.append(item.message.content)", "for item in (getattr(ret, \"choices\", None) or []):\n                outputs.append(getattr(item.message, \"content\", \"\") or \"\")\n            if not outputs: outputs = [\"\"] * num_samples"))'

WORKDIR /workspace

COPY ./containers/bigcodebench-entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
