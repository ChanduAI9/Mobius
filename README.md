# MOBIUS

**Personal AI Operating System**

MOBIUS is not a chatbot. It's your intelligent partner — a second brain for software engineering, startups, architecture, learning, and productivity.

```
◈ Think before answering
◈ Remember what matters
◈ Challenge weak ideas
◈ Explain trade-offs
◈ Grow smarter over time
```

## Features

### Phase 3 (Current)

- **Research Agent** — Web search (Tavily / DuckDuckGo), citations, comparisons, paper analysis, competitor research, auto-store to knowledge base
- **Plugin Connectors** — Notion and Google Drive via extensible plugin registry
- **Project Management** — Kanban, roadmaps, sprints, milestones, analytics, AI recommendations
- **Tool Orchestrator** — Multi-step planning across memory, KB, web, projects, and agents

### Phase 2

- **Knowledge Base** — GitHub + local folder ingestion, PDF/DOCX/MD support, hybrid RAG
- **Coding Agent** — Repository-aware code assistance with file citations
- **Architecture Agent** — Design review with Mermaid diagram generation
- **Orchestrator** — Intent-based agent routing integrated with chat
- **Source Watcher** — Automatic re-indexing on file changes

### Phase 1

- **Conversation** — Streaming chat with multi-provider LLM support (OpenAI, Anthropic, Ollama)
- **Authentication** — JWT with refresh tokens
- **Memory** — Semantic retrieval with pgvector, hybrid search, importance scoring
- **Idea Capture** — Auto-trigger on "I have an idea", structured startup analysis
- **Voice** — STT/TTS via OpenAI Whisper and TTS
- **Dashboard** — Focus, recommendations, quick actions
- **Search** — Cross-memory, idea, and conversation search

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- An API key from [OpenAI](https://platform.openai.com/) (recommended) or [Anthropic](https://console.anthropic.com/)

> **No GPU?** Use OpenAI/Anthropic for AI. Local Ollama works but is slow on CPU-only machines (e.g. Intel MacBook Air).

### Run with Docker

```bash
git clone https://github.com/YOUR_USERNAME/mobius.git
cd mobius
cp .env.example .env
# Edit .env — add OPENAI_API_KEY and a random JWT_SECRET_KEY

docker compose up -d
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Recommended | Chat, agents, voice, research synthesis |
| `ANTHROPIC_API_KEY` | Optional | Alternative LLM provider |
| `JWT_SECRET_KEY` | Production | Random secret for auth tokens |
| `TAVILY_API_KEY` | Optional | Web research (free tier available) |
| `NOTION_API_KEY` | Optional | Notion knowledge sync |
| `GOOGLE_DRIVE_ACCESS_TOKEN` | Optional | Google Drive knowledge sync |

See [Deployment Guide](docs/deployment/DEPLOYMENT.md) for production setup.

### Access from Phone (same Wi‑Fi)

MOBIUS runs on your computer; use your phone's browser to connect.

1. Find your computer's local IP: `ipconfig getifaddr en0` (Mac) or `hostname -I` (Linux)
2. Add to `.env`: `CORS_ORIGINS=http://localhost:3000,http://YOUR_IP:3000`
3. Set `NEXT_PUBLIC_API_URL=http://YOUR_IP:8000` in `docker-compose.yml` (frontend service)
4. Open `http://YOUR_IP:3000` on your phone

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Next.js    │────▶│   FastAPI    │────▶│  PostgreSQL    │
│  Frontend   │ WS  │   Backend    │     │  + pgvector    │
└─────────────┘     └──────┬───────┘     └────────────────┘
                           │
                    ┌──────┴───────┐
                    │ OpenAI       │
                    │ Anthropic    │
                    │ Ollama       │
                    └──────────────┘
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture/OVERVIEW.md) | System design, diagrams, tech stack |
| [Phase 2 Guide](docs/architecture/PHASE2.md) | Knowledge base, RAG, agents |
| [Phase 3 Guide](docs/architecture/PHASE3.md) | Research, plugins, PM, tool orchestrator |
| [Database Schema](docs/architecture/DATABASE_SCHEMA.md) | ERD, indexes, memory tiers |
| [API Specification](docs/api/API_SPECIFICATION.md) | REST + WebSocket endpoints |
| [Deployment Guide](docs/deployment/DEPLOYMENT.md) | Docker, production setup |
| [Developer Guide](docs/development/DEVELOPER_GUIDE.md) | Contributing, local dev |
| [User Guide](docs/user/USER_GUIDE.md) | End-user documentation |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Database | PostgreSQL 16 + pgvector |
| Embeddings | sentence-transformers (local, no API cost) |
| AI | OpenAI, Anthropic, Ollama |
| DevOps | Docker Compose, GitHub Actions |

## Project Structure

```
mobius/
├── backend/          # FastAPI application
├── frontend/         # Next.js application
├── docs/             # Architecture, API, guides
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Development

```bash
# Backend
cd backend && pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Tests
cd backend && pytest tests/unit/ -v
```

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for module-specific setup.

## Roadmap

- **Phase 1** ✅ Conversation, Auth, Memory, Ideas, Voice, Dashboard, Search
- **Phase 2** ✅ Knowledge Base, Coding Agent, Architecture Agent, RAG
- **Phase 3** ✅ Research Agent, Plugins, Project Management, Tool Orchestrator
- **Phase 4** — Mobile apps, Calendar, Email, Cross-device sync, Analytics

## License

MIT — see [LICENSE](LICENSE) for details.
