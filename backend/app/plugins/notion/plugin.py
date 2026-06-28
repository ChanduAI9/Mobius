import json
from typing import Any

import httpx

from app.config import settings
from app.domain.knowledge import ParsedDocument, compute_content_hash
from app.plugins.base import KnowledgeConnectorPlugin, PluginInfo


class NotionPlugin(KnowledgeConnectorPlugin):
    API_BASE = "https://api.notion.com/v1"

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="notion",
            version="1.0.0",
            description="Sync Notion pages and databases",
            source_type="notion",
            required_config=["token"],
        )

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    async def list_documents(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        token = config.get("token") or settings.notion_api_key
        if not token:
            raise ValueError("Notion API token required")

        database_id = config.get("database_id")
        page_ids = config.get("page_ids", [])

        docs: list[dict] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            if database_id:
                url = f"{self.API_BASE}/databases/{database_id}/query"
                response = await client.post(url, headers=self._headers(token), json={"page_size": 100})
                response.raise_for_status()
                for page in response.json().get("results", []):
                    page_id = page["id"]
                    title = self._extract_title(page)
                    docs.append({"path": f"notion/{page_id}.md", "id": page_id, "title": title})

            for page_id in page_ids:
                docs.append({"path": f"notion/{page_id}.md", "id": page_id, "title": page_id})

            if not database_id and not page_ids:
                url = f"{self.API_BASE}/search"
                response = await client.post(
                    url, headers=self._headers(token), json={"filter": {"value": "page", "property": "object"}}
                )
                response.raise_for_status()
                for page in response.json().get("results", []):
                    page_id = page["id"]
                    title = self._extract_title(page)
                    docs.append({"path": f"notion/{page_id}.md", "id": page_id, "title": title})

        return docs

    async def fetch_document(self, config: dict[str, Any], doc_ref: dict[str, Any]) -> ParsedDocument:
        token = config.get("token") or settings.notion_api_key
        page_id = doc_ref["id"]
        title = doc_ref.get("title", page_id)

        content = await self._fetch_page_blocks(token, page_id)
        return ParsedDocument(
            filename=f"{title}.md",
            file_path=doc_ref["path"],
            mime_type="text/markdown",
            content=content,
            content_hash=compute_content_hash(content),
            file_size=len(content.encode()),
            metadata={"notion_page_id": page_id, "source": "notion"},
        )

    async def _fetch_page_blocks(self, token: str, page_id: str) -> str:
        blocks: list[str] = []
        cursor = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {"page_size": 100}
                if cursor:
                    params["start_cursor"] = cursor
                url = f"{self.API_BASE}/blocks/{page_id}/children"
                response = await client.get(url, headers=self._headers(token), params=params)
                response.raise_for_status()
                data = response.json()
                for block in data.get("results", []):
                    text = self._block_to_text(block)
                    if text:
                        blocks.append(text)
                if not data.get("has_more"):
                    break
                cursor = data.get("next_cursor")
        return "\n\n".join(blocks)

    @staticmethod
    def _block_to_text(block: dict) -> str:
        block_type = block.get("type", "")
        content = block.get(block_type, {})
        rich_text = content.get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rich_text)
        if block_type.startswith("heading"):
            level = block_type[-1] if block_type[-1].isdigit() else "1"
            return f"{'#' * int(level)} {text}"
        if block_type == "bulleted_list_item":
            return f"- {text}"
        if block_type == "numbered_list_item":
            return f"1. {text}"
        if block_type == "code":
            lang = content.get("language", "")
            return f"```{lang}\n{text}\n```"
        return text

    @staticmethod
    def _extract_title(page: dict) -> str:
        props = page.get("properties", {})
        for key in ("title", "Name", "name"):
            if key in props:
                title_prop = props[key]
                if title_prop.get("type") == "title":
                    texts = title_prop.get("title", [])
                    return "".join(t.get("plain_text", "") for t in texts) or "Untitled"
        return "Untitled"
