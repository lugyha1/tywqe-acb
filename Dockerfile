FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml README.md ./
RUN uv sync --no-dev --no-install-project
COPY src ./src
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
CMD ["uv", "run", "bot"]
