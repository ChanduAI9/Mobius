from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MOBIUS"
    app_version: str = "0.3.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://mobius:mobius@localhost:5432/mobius"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production-use-256-bit-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:3000"

    default_llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    max_upload_size_mb: int = 25

    # Knowledge Base
    knowledge_storage_path: str = "./data/knowledge"
    github_token: str = ""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    rag_top_k: int = 10
    watcher_poll_interval_seconds: int = 60
    hybrid_vector_weight: float = 0.65
    hybrid_keyword_weight: float = 0.35

    # Research & integrations
    tavily_api_key: str = ""
    notion_api_key: str = ""
    google_drive_access_token: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
