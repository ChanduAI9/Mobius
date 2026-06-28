from app.domain.knowledge import ParsedDocument
from app.plugins.base import KnowledgeConnectorPlugin, PluginInfo


class PluginRegistry:
    _connectors: dict[str, type[KnowledgeConnectorPlugin]] = {}
    _instances: dict[str, KnowledgeConnectorPlugin] = {}

    @classmethod
    def register_connector(cls, source_type: str, plugin_class: type[KnowledgeConnectorPlugin]) -> None:
        cls._connectors[source_type] = plugin_class

    @classmethod
    def get_connector(cls, source_type: str) -> KnowledgeConnectorPlugin | None:
        if source_type not in cls._connectors:
            return None
        if source_type not in cls._instances:
            cls._instances[source_type] = cls._connectors[source_type]()
        return cls._instances[source_type]

    @classmethod
    def list_connectors(cls) -> list[PluginInfo]:
        return [cls._connectors[k]().info for k in cls._connectors]

    @classmethod
    async def fetch_all(cls, source_type: str, config: dict) -> list[ParsedDocument]:
        connector = cls.get_connector(source_type)
        if not connector:
            raise ValueError(f"No plugin registered for source type: {source_type}")
        await connector.initialize(config)
        doc_refs = await connector.list_documents(config)
        documents = []
        for ref in doc_refs:
            try:
                documents.append(await connector.fetch_document(config, ref))
            except Exception:
                continue
        return documents


def register_builtin_plugins() -> None:
    from app.plugins.gdrive.plugin import GoogleDrivePlugin
    from app.plugins.notion.plugin import NotionPlugin

    PluginRegistry.register_connector("notion", NotionPlugin)
    PluginRegistry.register_connector("google_drive", GoogleDrivePlugin)
