FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src ./src
COPY app-service ./app-service
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir uv && uv pip install --system .

CMD ["uvicorn", "main:app", "--app-dir", "app-service", "--host", "0.0.0.0", "--port", "8000"]
