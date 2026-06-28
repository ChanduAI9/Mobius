import json
from typing import Any

import httpx

from app.config import settings
from app.domain.knowledge import ParsedDocument, compute_content_hash
from app.plugins.base import KnowledgeConnectorPlugin, PluginInfo

EXPORT_MIMES = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
}


class GoogleDrivePlugin(KnowledgeConnectorPlugin):
    API_BASE = "https://www.googleapis.com/drive/v3"

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="google_drive",
            version="1.0.0",
            description="Sync Google Drive files and documents",
            source_type="google_drive",
            required_config=["access_token"],
        )

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    async def list_documents(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        token = config.get("access_token") or settings.google_drive_access_token
        if not token:
            raise ValueError("Google Drive access token required")

        folder_id = config.get("folder_id", "root")
        docs: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            query = f"'{folder_id}' in parents and trashed=false"
            page_token = None
            while True:
                params: dict = {
                    "q": query,
                    "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,size)",
                    "pageSize": 100,
                }
                if page_token:
                    params["pageToken"] = page_token
                response = await client.get(
                    f"{self.API_BASE}/files", headers=self._headers(token), params=params
                )
                response.raise_for_status()
                data = response.json()
                for f in data.get("files", []):
                    mime = f.get("mimeType", "")
                    if mime.startswith("application/vnd.google-apps") and mime not in EXPORT_MIMES:
                        if mime not in ("application/vnd.google-apps.folder",):
                            continue
                    if mime == "application/vnd.google-apps.folder":
                        continue
                    docs.append({
                        "path": f"gdrive/{f['id']}/{f['name']}",
                        "id": f["id"],
                        "name": f["name"],
                        "mimeType": mime,
                        "modifiedTime": f.get("modifiedTime"),
                    })
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        return docs

    async def fetch_document(self, config: dict[str, Any], doc_ref: dict[str, Any]) -> ParsedDocument:
        token = config.get("access_token") or settings.google_drive_access_token
        file_id = doc_ref["id"]
        name = doc_ref.get("name", "file")
        mime = doc_ref.get("mimeType", "text/plain")

        async with httpx.AsyncClient(timeout=60.0) as client:
            if mime in EXPORT_MIMES:
                export_mime = EXPORT_MIMES[mime]
                url = f"{self.API_BASE}/files/{file_id}/export"
                response = await client.get(
                    url, headers=self._headers(token), params={"mimeType": export_mime}
                )
            else:
                url = f"{self.API_BASE}/files/{file_id}"
                response = await client.get(
                    url, headers=self._headers(token), params={"alt": "media"}
                )
            response.raise_for_status()
            raw = response.content

        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("latin-1", errors="replace")

        return ParsedDocument(
            filename=name,
            file_path=doc_ref["path"],
            mime_type=mime,
            content=content,
            content_hash=compute_content_hash(content),
            file_size=len(raw),
            metadata={
                "gdrive_file_id": file_id,
                "source": "google_drive",
                "modifiedTime": doc_ref.get("modifiedTime"),
            },
        )
