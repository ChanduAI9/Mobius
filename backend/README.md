# MOBIUS Backend

FastAPI application powering MOBIUS — auth, memory, knowledge base, agents, research, and project management.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp ../.env.example ../.env    # configure from repo root
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation: http://localhost:8000/docs

## Structure

```
app/
├── api/routes/          # REST + WebSocket endpoints
├── application/         # Business logic (services, agents, tools)
├── domain/              # Entities and value objects
├── infrastructure/      # DB, AI providers, connectors, research
└── plugins/             # Notion, Google Drive connectors
```

## Key Modules

| Module | Path | Purpose |
|--------|------|---------|
| Auth | `application/auth/` | JWT registration, login, refresh |
| Memory | `application/memory/` | Semantic memory with pgvector |
| Knowledge | `application/knowledge/` | RAG, ingestion, hybrid search |
| Agents | `application/agents/` | Coding, architecture, research agents |
| Research | `application/research/` | Web search, citations, comparisons |
| Projects | `application/projects/` | Kanban, sprints, milestones |
| Tools | `application/tools/` | Multi-step tool orchestrator |

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Tests

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v   # requires running Postgres
```

## Environment

Reads from `../.env` at repo root. Minimum for development:

```env
DATABASE_URL=postgresql+asyncpg://mobius:mobius@localhost:5432/mobius
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=dev-secret-change-me
```
