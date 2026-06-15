# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
COPY app/ ./app/
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.13-slim AS runtime

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

COPY --from=builder /usr/local /usr/local

COPY app/ ./app/
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY bootstrap_admin.py ./

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
