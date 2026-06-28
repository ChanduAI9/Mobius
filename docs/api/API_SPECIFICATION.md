# MOBIUS API Specification

Base URL: `http://localhost:8000/api/v1`

All authenticated endpoints require header: `Authorization: Bearer <access_token>`

## Authentication

### POST /auth/register

Register a new user.

**Request**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "display_name": "Saichandu"
}
```

**Response 201**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "Saichandu",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /auth/login

**Request**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response 200** — Same as register response.

### POST /auth/refresh

**Request**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response 200**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### GET /auth/me

**Response 200**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "Saichandu",
  "preferences": {},
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## Conversations

### GET /conversations

List user conversations.

**Query**: `limit=20`, `offset=0`, `project_id=uuid`

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Architecture discussion",
      "status": "active",
      "project_id": null,
      "message_count": 12,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-02T00:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /conversations

**Request**
```json
{
  "title": "New conversation",
  "project_id": null
}
```

### GET /conversations/{id}

Returns conversation with messages.

### POST /conversations/{id}/messages

Send a message (non-streaming).

**Request**
```json
{
  "content": "Help me design a microservices architecture",
  "attachments": []
}
```

**Response 200**
```json
{
  "user_message": { "id": "uuid", "role": "user", "content": "..." },
  "assistant_message": { "id": "uuid", "role": "assistant", "content": "..." }
}
```

### WebSocket /ws/conversations/{id}

Streaming conversation.

**Client sends**
```json
{
  "type": "message",
  "content": "Hello MOBIUS"
}
```

**Server sends**
```json
{ "type": "token", "content": "Hello" }
{ "type": "token", "content": "!" }
{ "type": "done", "message_id": "uuid" }
{ "type": "error", "message": "..." }
```

---

## Memories

### GET /memories

**Query**: `tier=long_term`, `category=preference`, `limit=50`, `offset=0`

### POST /memories

**Request**
```json
{
  "content": "Prefers FastAPI over Flask for new projects",
  "category": "preference",
  "tier": "long_term",
  "importance": 0.8,
  "tags": ["coding", "python"],
  "project_id": null
}
```

### GET /memories/{id}

### PATCH /memories/{id}

### DELETE /memories/{id}

### POST /memories/search

Semantic search.

**Request**
```json
{
  "query": "What are my coding preferences?",
  "limit": 10,
  "tiers": ["long_term", "semantic"],
  "min_importance": 0.0
}
```

**Response 200**
```json
{
  "results": [
    {
      "memory": { "id": "uuid", "content": "...", "importance": 0.8 },
      "score": 0.92
    }
  ]
}
```

---

## Ideas

### GET /ideas

### POST /ideas

Manual idea capture.

**Request**
```json
{
  "raw_input": "A platform for async video discussions",
  "project_id": null
}
```

**Response 201** — Full idea with analysis.

### POST /ideas/capture

Auto-trigger from conversation text. Detects "I have an idea" patterns.

**Request**
```json
{
  "content": "I have an idea for a meeting platform that uses async video",
  "conversation_id": "uuid"
}
```

**Response 201**
```json
{
  "id": "uuid",
  "summary": "...",
  "business_value": "...",
  "implementation_effort": "...",
  "weaknesses": "...",
  "improvements": "...",
  "analysis": {
    "feasibility": 0.7,
    "complexity": "medium",
    "market_potential": "high",
    "confidence": 0.75
  },
  "tasks": [
    { "title": "Validate problem with 10 users", "priority": "high" }
  ],
  "related_ideas": []
}
```

### GET /ideas/{id}

### PATCH /ideas/{id}

---

## Search

### GET /search

Global search across memories, conversations, ideas.

**Query**: `q=authentication`, `types=memories,ideas,conversations`, `limit=20`

**Response 200**
```json
{
  "results": [
    {
      "type": "memory",
      "id": "uuid",
      "title": "Auth architecture",
      "snippet": "...JWT with refresh rotation...",
      "score": 0.89
    }
  ]
}
```

---

## Voice

### POST /voice/transcribe

Upload audio file for STT.

**Request**: `multipart/form-data` with `file` (audio/webm, audio/wav, audio/mp3)

**Response 200**
```json
{
  "text": "I have an idea for a new startup",
  "duration_seconds": 3.2
}
```

### POST /voice/synthesize

**Request**
```json
{
  "text": "Hello, I'm MOBIUS.",
  "voice": "alloy"
}
```

**Response 200**: `audio/mpeg` binary stream

---

## Dashboard

### GET /dashboard

**Response 200**
```json
{
  "focus": {
    "title": "Continue Meet2Discuss authentication",
    "reason": "Planned for this week, last touched 4 days ago"
  },
  "recent_memories": [],
  "recent_ideas": [],
  "upcoming_tasks": [],
  "recommendations": [
    {
      "type": "proactive",
      "message": "You haven't touched Meet2Discuss in four days.",
      "action_url": "/projects/meet2discuss"
    }
  ],
  "stats": {
    "conversations_today": 3,
    "memories_total": 142,
    "ideas_total": 8
  }
}
```

---

## Health

### GET /health

**Response 200**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "redis": "connected"
}
```

---

## Error Format

```json
{
  "detail": "Human-readable message",
  "code": "VALIDATION_ERROR",
  "errors": []
}
```

| Status | Meaning |
|--------|---------|
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 429 | Rate limited |
| 500 | Internal error |
