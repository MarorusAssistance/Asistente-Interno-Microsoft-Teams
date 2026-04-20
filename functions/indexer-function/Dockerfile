FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src ./src
COPY functions/indexer-function ./functions/indexer-function

RUN pip install --no-cache-dir uv && uv pip install --system .

CMD ["uvicorn", "local_main:app", "--app-dir", "functions/indexer-function", "--host", "0.0.0.0", "--port", "7071"]
