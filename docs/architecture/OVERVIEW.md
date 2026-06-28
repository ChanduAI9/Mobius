# MOBIUS — System Architecture Overview

## Vision

MOBIUS is a personal AI operating system: a modular, secure, extensible platform that acts as a second brain, advisor, and intelligent partner—not a chatbot.

## Architectural Principles

| Principle | Decision | Trade-off |
|-----------|----------|-----------|
| **Modularity** | Feature-based modules with clean boundaries | Slightly more boilerplate; vastly easier to extend |
| **Privacy-first** | User data encrypted at rest; local LLM support via Ollama | More config complexity vs. cloud-only |
| **Semantic memory** | pgvector + hybrid search + reranking | PostgreSQL dependency vs. separate vector DB |
| **Multi-provider AI** | Pluggable provider abstraction with routing/fallback | Abstraction layer overhead vs. vendor lock-in |
| **Async-first** | FastAPI + async SQLAlchemy + WebSockets | Learning curve vs. throughput under load |
| **Plugin-ready** | Core exposes hooks; integrations are plugins | Initial plugin API is minimal in Phase 1 |

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Clients["Client Layer"]
        WEB[Web App - Next.js]
        DESK[Desktop - Tauri/Electron]
        MOB[Mobile - Flutter/Android]
        VOICE[Voice Pipeline]
    end

    subgraph Gateway["API Gateway"]
        REST[REST API]
        WS[WebSocket - Streaming]
        AUTH[JWT Auth + Rate Limiting]
    end

    subgraph Core["MOBIUS Core"]
        ORCH[Orchestrator - Phase 4]
        CONV[Conversation Service]
        MEM[Memory Service]
        IDEA[Idea Capture Service]
        SEARCH[Search Service]
        VOICE_SVC[Voice Service]
    end

    subgraph Agents["Specialized Agents - Phase 2+"]
        CODE[Coding Agent]
        ARCH[Architecture Agent]
        RES[Research Agent]
        PM[Project Manager]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL + pgvector)]
        REDIS[(Redis - Queue/Cache)]
        S3[Object Storage - Docs]
    end

    subgraph AI["AI Providers"]
        OPENAI[OpenAI]
        ANTHropic[Anthropic]
        GEMINI[Google Gemini]
        OLLAMA[Ollama / Local]
    end

    WEB --> Gateway
    DESK --> Gateway
    MOB --> Gateway
    VOICE --> Gateway

    Gateway --> Core
    Core --> Agents
    Core --> Data
    Core --> AI
    Agents --> AI
    Agents --> Data
```

## Memory Architecture

```mermaid
flowchart LR
    subgraph Input
        MSG[Conversation]
        DOC[Documents]
        IDEA_IN[Idea Capture]
    end

    subgraph Tiers["Memory Tiers"]
        WM[Working Memory - Session Context]
        STM[Short-Term - Recent 24-72h]
        LTM[Long-Term - Persistent]
        PM[Project Memory]
        SM[Semantic - Embeddings]
        AM[Archived - Cold Storage]
        RM[Reflection - Consolidated Insights]
    end

    subgraph Ops["Operations"]
        SCORE[Importance Scoring]
        CONS[Consolidation Worker]
        PRUNE[Pruning Worker]
        RET[Semantic Retrieval]
    end

    Input --> WM
    WM --> STM
    STM --> SCORE
    SCORE --> LTM
    LTM --> SM
    LTM --> PM
    LTM --> AM
    CONS --> RM
    PRUNE --> AM
    SM --> RET
```

## Request Flow (Phase 1 Conversation)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant C as ConversationService
    participant M as MemoryService
    participant E as EmbeddingService
    participant L as LLMProvider

    U->>F: Send message
    F->>A: POST /conversations/{id}/messages (WS stream)
    A->>C: process_message()
    C->>M: retrieve_relevant_memories(query)
    M->>E: embed(query)
    E-->>M: vector
    M-->>C: top-k memories
    C->>L: stream_completion(system + memories + history)
    L-->>C: token stream
    C-->>F: SSE/WebSocket chunks
    C->>M: store_message + extract_memories
    F-->>U: Render streaming response
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Database | PostgreSQL 16 + pgvector |
| Cache/Queue | Redis 7 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| AI | OpenAI, Anthropic, Google, Ollama (abstracted) |
| Auth | JWT (access + refresh), bcrypt passwords |
| DevOps | Docker Compose, GitHub Actions |
| Voice | Whisper STT, OpenAI TTS (Phase 1) |

## Security Model

- All API routes require authentication (except health/register/login)
- Secrets via environment variables; never committed
- Passwords hashed with bcrypt
- JWT short-lived access tokens + refresh rotation
- Rate limiting per user/IP
- Input validation on all endpoints
- Audit log for sensitive operations
- TLS in production (reverse proxy)

## Scalability Path

1. **Phase 1**: Single-node Docker Compose
2. **Phase 2**: Horizontal API replicas + Redis session
3. **Phase 3**: Background workers for indexing, consolidation
4. **Phase 4**: Multi-agent orchestrator with dedicated worker pools

## Folder Structure

See [FOLDER_STRUCTURE.md](./FOLDER_STRUCTURE.md).

## Related Documents

- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)
- [API_SPECIFICATION.md](../api/API_SPECIFICATION.md)
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
- [WIREFRAMES.md](../design/WIREFRAMES.md)
- [TESTING_STRATEGY.md](../development/TESTING_STRATEGY.md)
- [DEPLOYMENT.md](../deployment/DEPLOYMENT.md)
- [SECURITY_CHECKLIST.md](../security/SECURITY_CHECKLIST.md)
