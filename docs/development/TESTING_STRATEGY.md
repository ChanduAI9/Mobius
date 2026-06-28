# MOBIUS Testing Strategy

## Test Pyramid

```
        ┌─────────┐
        │   E2E   │  Few, critical user flows
        ├─────────┤
        │ Integr. │  API endpoints, DB, AI mocks
        ├─────────┤
        │  Unit   │  Services, utilities, domain logic
        └─────────┘
```

## Backend Tests

### Unit Tests (`tests/unit/`)

| Module | What to Test |
|--------|--------------|
| `auth_service` | Password validation, token creation |
| `memory_service` | Importance scoring, tier logic |
| `idea_service` | Idea trigger detection |
| `search_service` | Result ranking, filtering |
| `jwt` | Token encode/decode, expiry |
| `password` | Hash/verify |

### Integration Tests (`tests/integration/`)

| Test | Description |
|------|-------------|
| Auth flow | Register → login → refresh → me |
| Conversation | Create → send message → list messages |
| Memory CRUD | Create → search → update → delete |
| Idea capture | POST capture → verify analysis fields |
| Search | Index memories → query → verify results |
| Health | GET /health returns 200 |

### Test Infrastructure

- **Database**: Test PostgreSQL with pgvector (or SQLite for unit-only)
- **Fixtures**: `conftest.py` with async session, test user, auth headers
- **AI mocking**: Mock `LLMProvider` to return deterministic responses
- **Embeddings**: Mock embedding service in unit tests; real in integration

### Running Tests

```bash
cd backend
pytest                          # All tests
pytest tests/unit/              # Unit only
pytest tests/integration/       # Integration only
pytest --cov=app --cov-report=term-missing
```

## Frontend Tests (Phase 2+)

- **Type checking**: `tsc --noEmit`
- **Lint**: ESLint
- **Component tests**: Vitest + React Testing Library
- **E2E**: Playwright for login → chat → dashboard flow

## Performance Tests (Phase 2+)

- Memory search latency < 200ms for 10k memories
- Conversation first-token latency < 2s
- Dashboard load < 500ms

## Security Tests

- Auth endpoints reject invalid tokens
- Users cannot access other users' data
- Rate limiting triggers after threshold
- File upload rejects oversized/invalid files

## CI Pipeline

Every push to `main` or PR:

1. `ruff check app/`
2. `pytest tests/`
3. `npm run lint && npm run type-check` (frontend)

## Coverage Targets

| Phase | Target |
|-------|--------|
| Phase 1 | 70% backend service coverage |
| Phase 2 | 80% + integration for all routes |
| Phase 3 | E2E for critical flows |
