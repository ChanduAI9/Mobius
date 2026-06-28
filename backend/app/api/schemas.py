from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    preferences: dict = {}
    created_at: str


class AuthResponse(TokenResponse):
    id: str
    email: str
    display_name: str


class CreateConversationRequest(BaseModel):
    title: str = "New conversation"
    project_id: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)
    attachments: list = []


class CreateMemoryRequest(BaseModel):
    content: str = Field(min_length=1)
    category: str = "general"
    tier: str = "long_term"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = []
    project_id: str | None = None
    summary: str | None = None


class UpdateMemoryRequest(BaseModel):
    content: str | None = None
    category: str | None = None
    tier: str | None = None
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    tags: list[str] | None = None
    summary: str | None = None


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    tiers: list[str] | None = None
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)


class CreateIdeaRequest(BaseModel):
    raw_input: str = Field(min_length=1)
    project_id: str | None = None


class CaptureIdeaRequest(BaseModel):
    content: str = Field(min_length=1)
    conversation_id: str | None = None
    project_id: str | None = None


class UpdateIdeaRequest(BaseModel):
    status: str | None = None
    summary: str | None = None


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    voice: str = "alloy"
