# MOBIUS Database Schema

PostgreSQL 16 with `pgvector` extension.

## Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ conversations : has
    users ||--o{ memories : owns
    users ||--o{ ideas : owns
    users ||--o{ projects : owns
    users ||--o{ documents : owns
    users ||--o{ audit_logs : generates

    conversations ||--o{ messages : contains
    conversations }o--o| projects : linked_to

    memories }o--o| projects : belongs_to
    memories }o--o{ memory_tags : tagged
    memories ||--o{ memory_relationships : source
    memories ||--o{ memory_relationships : target

    ideas }o--o| projects : linked_to
    ideas ||--o{ idea_tasks : generates

    projects ||--o{ tasks : contains

    tags ||--o{ memory_tags : used_in

    users {
        uuid id PK
        string email UK
        string password_hash
        string display_name
        jsonb preferences
        timestamp created_at
        timestamp updated_at
    }

    conversations {
        uuid id PK
        uuid user_id FK
        uuid project_id FK
        string title
        string status
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    messages {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        jsonb attachments
        jsonb metadata
        timestamp created_at
    }

    memories {
        uuid id PK
        uuid user_id FK
        uuid project_id FK
        string tier
        string category
        text content
        text summary
        float importance
        vector embedding
        tsvector search_vector
        string source_type
        uuid source_id
        jsonb metadata
        timestamp expires_at
        timestamp created_at
        timestamp updated_at
    }

    ideas {
        uuid id PK
        uuid user_id FK
        uuid project_id FK
        text raw_input
        text summary
        text business_value
        text implementation_effort
        text weaknesses
        text improvements
        jsonb analysis
        string status
        timestamp created_at
        timestamp updated_at
    }

    projects {
        uuid id PK
        uuid user_id FK
        string name
        text description
        string status
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    tasks {
        uuid id PK
        uuid project_id FK
        uuid idea_id FK
        string title
        text description
        string status
        string priority
        date due_date
        timestamp created_at
        timestamp updated_at
    }

    documents {
        uuid id PK
        uuid user_id FK
        uuid project_id FK
        string filename
        string mime_type
        string storage_path
        text extracted_text
        vector embedding
        jsonb metadata
        timestamp created_at
    }

    tags {
        uuid id PK
        string name UK
    }

    memory_tags {
        uuid memory_id FK
        uuid tag_id FK
    }

    memory_relationships {
        uuid id PK
        uuid source_memory_id FK
        uuid target_memory_id FK
        string relationship_type
        float strength
    }

    audit_logs {
        uuid id PK
        uuid user_id FK
        string action
        string resource_type
        uuid resource_id
        jsonb details
        string ip_address
        timestamp created_at
    }

    refresh_tokens {
        uuid id PK
        uuid user_id FK
        string token_hash
        timestamp expires_at
        timestamp created_at
    }
```

## Memory Tiers

| Tier | Code | Retention | Use Case |
|------|------|-----------|----------|
| Working | `working` | Session | Current conversation context |
| Short-Term | `short_term` | 72 hours | Recent interactions |
| Long-Term | `long_term` | Permanent | Important facts, preferences |
| Project | `project` | Project lifetime | Architecture, goals |
| Semantic | `semantic` | Permanent | Embedding-indexed knowledge |
| Archived | `archived` | Permanent (cold) | Low-importance historical |
| Reflection | `reflection` | Permanent | Consolidated insights |

## Indexes

```sql
-- Vector similarity (HNSW for performance)
CREATE INDEX idx_memories_embedding ON memories USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_documents_embedding ON documents USING hnsw (embedding vector_cosine_ops);

-- Full-text search
CREATE INDEX idx_memories_search ON memories USING gin (search_vector);
CREATE INDEX idx_documents_text ON documents USING gin (to_tsvector('english', extracted_text));

-- Query patterns
CREATE INDEX idx_memories_user_tier ON memories (user_id, tier);
CREATE INDEX idx_memories_importance ON memories (user_id, importance DESC);
CREATE INDEX idx_messages_conversation ON messages (conversation_id, created_at);
CREATE INDEX idx_ideas_user_status ON ideas (user_id, status);
```

## Migration Strategy

Alembic manages schema evolution. Each phase adds migrations incrementally without breaking existing data.
