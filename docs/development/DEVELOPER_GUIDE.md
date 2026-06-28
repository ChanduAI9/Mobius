# MOBIUS Developer Guide

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL with pgvector (or use Docker)

### Setup

```bash
cp .env.example .env
# Add your OPENAI_API_KEY or ANTHROPIC_API_KEY

docker compose up -d postgres redis
cd backend && pip install -e ".[dev]" && alembic upgrade head
cd ../frontend && npm install
```

### Run locally

```bash
# Terminal 1 — Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend && npm run dev
```

## Architecture

MOBIUS follows **Clean Architecture** with four layers:

| Layer | Path | Responsibility |
|-------|------|----------------|
| Domain | `app/domain/` | Entities, interfaces (no I/O) |
| Application | `app/application/` | Business logic, use cases |
| Infrastructure | `app/infrastructure/` | DB, AI, embeddings, security |
| API | `app/api/` | HTTP/WebSocket routes |

## Adding a New Feature

1. Define entity in `domain/entities/`
2. Add repository interface in `domain/interfaces/`
3. Implement repository in `infrastructure/database/repositories/`
4. Create service in `application/<feature>/`
5. Add Pydantic schemas in `api/schemas.py`
6. Create route in `api/routes/`
7. Register router in `api/router.py`
8. Write tests in `tests/`

## Adding an AI Provider

1. Create provider class in `infrastructure/ai/` implementing `complete()` and `stream()`
2. Register in `LLMProviderRegistry` in `provider_registry.py`
3. Add config vars in `config.py` and `.env.example`

## Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Code Quality

```bash
# Backend lint
ruff check app/

# Backend tests
pytest tests/ -v --cov=app

# Frontend
npm run lint && npm run type-check
```

## Plugin System (Phase 4)

Future plugins implement the `Plugin` protocol:

```python
class Plugin(Protocol):
    name: str
    async def initialize(self, config: dict) -> None: ...
    async def execute(self, action: str, params: dict) -> dict: ...
```

Register via `plugins/registry.py` (Phase 4).

## Key Design Decisions

See [IMPLEMENTATION_PLAN.md](../docs/architecture/IMPLEMENTATION_PLAN.md) for ADRs.
