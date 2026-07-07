# Media Downloader Pro

A production-ready Telegram bot template rebuilt with Clean Architecture, aiogram 3.x, async SQLAlchemy, Redis FSM storage, Alembic migrations, Docker, and modern quality tooling.

## Architecture map

- `presentation` — aiogram routers, handlers, middlewares, keyboards, filters, FSM states.
- `application` — use cases and orchestration services.
- `domain` — framework-independent entities, interfaces, and repository contracts.
- `infrastructure` — database, Redis, Telegram, and external API adapters.
- `config`, `logging`, `core`, `shared`, `utils` — cross-cutting concerns.

The provided source snapshot contained only a placeholder `README.md`, so the bot was rebuilt as an extensible premium media-downloader product while preserving the described business goal: accept supported media links, create download jobs, show profile/history/help/settings screens, and provide a polished Telegram UX.

## Run locally

```bash
cp .env.example .env
uv sync --dev
uv run alembic upgrade head
uv run bot
```

## Docker

```bash
docker compose up --build
```

## Quality gates

```bash
uv run ruff check .
uv run black --check .
uv run mypy src
uv run pytest
```
