FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir evalplus openai rich tenacity && \
    python3 -c 'p="/usr/local/lib/python3.11/site-packages/evalplus/sanitize.py"; c=open(p).read(); open(p,"w").write(c.replace("def code_extract(text: str) -> str:\n", "def code_extract(text: str) -> str:\n    if not text: return \"\"\n"))' && \
    python3 -c 'p="/usr/local/lib/python3.11/site-packages/evalplus/provider/openai.py"; c=open(p).read(); open(p,"w").write(c.replace("for item in ret.choices:\n            outputs.append(item.message.content)", "for item in (getattr(ret, \"choices\", None) or []):\n            outputs.append(getattr(item.message, \"content\", \"\") or \"\")\n        if not outputs: outputs = [\"\"] * batch_size"))'

WORKDIR /workspace

# evalplus will output samples and evaluation results to /workspace
ENTRYPOINT ["python", "-m", "evalplus.evaluate"]
