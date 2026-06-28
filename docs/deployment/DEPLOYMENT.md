# MOBIUS Deployment Guide

## Prerequisites

- Docker & Docker Compose v2
- Node.js 20+ (local frontend dev)
- Python 3.12+ (local backend dev)
- At least one AI provider API key (OpenAI recommended)

## Quick Start (Docker)

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your secrets

# Start all services
docker compose up -d

# Run migrations
docker compose exec backend alembic upgrade head

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET_KEY` | Yes | Random 256-bit secret |
| `OPENAI_API_KEY` | One of | OpenAI API key |
| `ANTHROPIC_API_KEY` | One of | Anthropic API key |
| `DEFAULT_LLM_PROVIDER` | No | `openai` (default), `anthropic`, `ollama` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `EMBEDDING_MODEL` | No | Default: `all-MiniLM-L6-v2` |

See `.env.example` for full list.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database only

```bash
docker compose up -d postgres redis
```

## Production Deployment

### Recommended Architecture

```
Internet → Nginx/Caddy (TLS) → Frontend (static/SSR)
                             → Backend API (uvicorn workers)
                             → PostgreSQL
                             → Redis
```

### Backend Production

```bash
# Build
docker build -t mobius-backend ./backend

# Run with gunicorn + uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend Production

```bash
cd frontend
npm run build
npm start
# Or deploy to Vercel with NEXT_PUBLIC_API_URL set
```

### Database

- Enable automated backups (daily minimum)
- Use managed PostgreSQL with pgvector (Supabase, RDS, etc.)
- Connection pooling via PgBouncer for high traffic

### Monitoring

- Health check: `GET /api/v1/health`
- Structured JSON logs to stdout
- Recommended: Prometheus metrics + Grafana (Phase 2)
- Recommended: Sentry for error tracking

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):

1. Lint backend (ruff) and frontend (eslint)
2. Run backend unit + integration tests
3. Run frontend type check
4. Build Docker images on main branch

## Scaling

| Load | Configuration |
|------|---------------|
| Single user | Docker Compose on one machine |
| Small team | 2 API replicas + managed DB |
| Production | Load balancer + 4+ workers + Redis cluster |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| pgvector extension missing | Run `CREATE EXTENSION vector;` in PostgreSQL |
| Embedding model slow on first run | Model downloads on first use; wait or pre-bake in Docker |
| CORS errors | Add frontend URL to `CORS_ORIGINS` |
| JWT expired | Use refresh token endpoint |
| Ollama connection refused | Ensure Ollama running at configured URL |
