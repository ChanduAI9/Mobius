# MOBIUS Folder Structure

```
mobius/
├── README.md
├── docker-compose.yml
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docs/
│   ├── architecture/
│   │   ├── OVERVIEW.md
│   │   ├── DATABASE_SCHEMA.md
│   │   ├── IMPLEMENTATION_PLAN.md
│   │   └── FOLDER_STRUCTURE.md
│   ├── api/
│   │   └── API_SPECIFICATION.md
│   ├── design/
│   │   └── WIREFRAMES.md
│   ├── deployment/
│   │   └── DEPLOYMENT.md
│   ├── development/
│   │   ├── DEVELOPER_GUIDE.md
│   │   └── TESTING_STRATEGY.md
│   ├── security/
│   │   └── SECURITY_CHECKLIST.md
│   └── user/
│       └── USER_GUIDE.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── dependencies.py
│       │
│       ├── domain/                    # Pure business entities & interfaces
│       │   ├── entities/
│       │   │   ├── user.py
│       │   │   ├── conversation.py
│       │   │   ├── memory.py
│       │   │   └── idea.py
│       │   └── interfaces/
│       │       ├── llm_provider.py
│       │       ├── memory_repository.py
│       │       └── embedding_service.py
│       │
│       ├── application/               # Use cases & services
│       │   ├── auth/
│       │   │   └── auth_service.py
│       │   ├── conversation/
│       │   │   └── conversation_service.py
│       │   ├── memory/
│       │   │   └── memory_service.py
│       │   ├── ideas/
│       │   │   └── idea_service.py
│       │   ├── search/
│       │   │   └── search_service.py
│       │   ├── voice/
│       │   │   └── voice_service.py
│       │   └── dashboard/
│       │       └── dashboard_service.py
│       │
│       ├── infrastructure/            # External implementations
│       │   ├── database/
│       │   │   ├── session.py
│       │   │   ├── models/
│       │   │   └── repositories/
│       │   ├── ai/
│       │   │   ├── openai_provider.py
│       │   │   ├── anthropic_provider.py
│       │   │   ├── ollama_provider.py
│       │   │   └── provider_registry.py
│       │   ├── embeddings/
│       │   │   └── sentence_transformer.py
│       │   └── security/
│       │       ├── jwt.py
│       │       ├── password.py
│       │       └── rate_limiter.py
│       │
│       └── api/                       # HTTP layer
│           ├── router.py
│           ├── middleware/
│           │   └── audit.py
│           └── routes/
│               ├── auth.py
│               ├── conversations.py
│               ├── memories.py
│               ├── ideas.py
│               ├── search.py
│               ├── voice.py
│               ├── dashboard.py
│               └── health.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx                 # Dashboard
        │   ├── globals.css
        │   ├── (auth)/
        │   │   ├── login/page.tsx
        │   │   └── register/page.tsx
        │   ├── chat/
        │   │   └── page.tsx
        │   ├── memories/
        │   │   └── page.tsx
        │   ├── ideas/
        │   │   └── page.tsx
        │   └── search/
        │       └── page.tsx
        ├── components/
        │   ├── layout/
        │   │   ├── Sidebar.tsx
        │   │   └── Header.tsx
        │   ├── dashboard/
        │   │   ├── FocusWidget.tsx
        │   │   ├── MemoriesWidget.tsx
        │   │   ├── IdeasWidget.tsx
        │   │   └── RecommendationsWidget.tsx
        │   ├── chat/
        │   │   ├── ChatInterface.tsx
        │   │   └── MessageBubble.tsx
        │   └── ui/
        │       ├── Button.tsx
        │       ├── Input.tsx
        │       └── Card.tsx
        ├── lib/
        │   ├── api.ts
        │   ├── auth.ts
        │   └── websocket.ts
        └── types/
            └── index.ts
```

## Module Boundaries

Each backend feature follows:

```
domain/entities     → Pure dataclasses, no I/O
domain/interfaces   → Protocols/ABCs
application/        → Business logic, orchestration
infrastructure/     → DB, AI, external APIs
api/routes/         → HTTP mapping only
```

Future agents (Phase 2+) add under `application/agents/`:

```
application/agents/
├── coding_agent.py
├── architecture_agent.py
├── research_agent.py
└── orchestrator.py          # Phase 4
```

Future plugins (Phase 4+) add under `plugins/`:

```
plugins/
├── base.py                  # Plugin protocol
├── github/
├── notion/
└── registry.py
```
