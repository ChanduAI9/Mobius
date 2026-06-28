from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.domain.knowledge import ParsedDocument


@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    source_type: str
    required_config: list[str] = field(default_factory=list)


class Plugin(Protocol):
    @property
    def info(self) -> PluginInfo: ...

    async def initialize(self, config: dict[str, Any]) -> None: ...

    async def health_check(self) -> bool: ...


class KnowledgeConnectorPlugin(ABC):
    """Plugin interface for knowledge base connectors."""

    @property
    @abstractmethod
    def info(self) -> PluginInfo: ...

    async def initialize(self, config: dict[str, Any]) -> None:
        self._config = config

    async def health_check(self) -> bool:
        return True

    @abstractmethod
    async def list_documents(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Return list of {path, id, metadata} for each document."""

    @abstractmethod
    async def fetch_document(self, config: dict[str, Any], doc_ref: dict[str, Any]) -> ParsedDocument:
        ...

    async def get_sync_cursor(self, config: dict[str, Any], documents: list[dict]) -> dict:
        return {d["path"]: d.get("hash", d.get("id", "")) for d in documents}
