from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MemoryTier(StrEnum):
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    PROJECT = "project"
    SEMANTIC = "semantic"
    ARCHIVED = "archived"
    REFLECTION = "reflection"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IdeaStatus(StrEnum):
    NEW = "new"
    REVIEWING = "reviewing"
    ACTIVE = "active"
    ARCHIVED = "archived"


class UserEntity(BaseModel):
    id: UUID
    email: str
    display_name: str
    preferences: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class MessageEntity(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    attachments: list = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class ConversationEntity(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    status: str = "active"
    project_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    messages: list[MessageEntity] = Field(default_factory=list)


class MemoryEntity(BaseModel):
    id: UUID
    user_id: UUID
    project_id: UUID | None = None
    tier: MemoryTier
    category: str
    content: str
    summary: str | None = None
    importance: float = 0.5
    source_type: str | None = None
    source_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class IdeaEntity(BaseModel):
    id: UUID
    user_id: UUID
    project_id: UUID | None = None
    raw_input: str
    summary: str | None = None
    business_value: str | None = None
    implementation_effort: str | None = None
    weaknesses: str | None = None
    improvements: str | None = None
    analysis: dict = Field(default_factory=dict)
    status: IdeaStatus = IdeaStatus.NEW
    created_at: datetime
    updated_at: datetime


class TaskEntity(BaseModel):
    id: UUID
    project_id: UUID | None = None
    idea_id: UUID | None = None
    title: str
    description: str | None = None
    status: str = "pending"
    priority: str = "medium"
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
