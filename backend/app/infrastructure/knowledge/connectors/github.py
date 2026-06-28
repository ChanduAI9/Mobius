import base64
from typing import Any

import httpx

from app.config import settings
from app.domain.knowledge import SUPPORTED_EXTENSIONS, ParsedDocument, should_ignore_path
from app.infrastructure.knowledge.parsers import DocumentParser


class GitHubConnector:
    API_BASE = "https://api.github.com"

    def __init__(self, token: str | None = None, parser: DocumentParser | None = None) -> None:
        self._token = token or settings.github_token
        self._parser = parser or DocumentParser()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @staticmethod
    def parse_repo_url(repo: str) -> tuple[str, str]:
        repo = repo.rstrip("/")
        if repo.startswith("https://github.com/"):
            parts = repo.replace("https://github.com/", "").split("/")
        else:
            parts = repo.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub repo: {repo}")
        return parts[0], parts[1]

    async def list_files(
        self,
        owner: str,
        repo: str,
        *,
        branch: str = "main",
        path: str = "",
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            tree_url = f"{self.API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            response = await client.get(tree_url, headers=self._headers())
            if response.status_code == 404 and branch == "main":
                return await self.list_files(owner, repo, branch="master", path=path)
            response.raise_for_status()
            tree = response.json().get("tree", [])

        files = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            file_path = item["path"]
            if should_ignore_path(file_path):
                continue
            ext = f".{file_path.rsplit('.', 1)[-1].lower()}" if "." in file_path else ""
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            if path and not file_path.startswith(path):
                continue
            files.append({
                "path": file_path,
                "sha": item.get("sha"),
                "size": item.get("size", 0),
            })
        return files

    async def fetch_file(
        self,
        owner: str,
        repo: str,
        file_path: str,
        *,
        branch: str = "main",
    ) -> ParsedDocument:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{self.API_BASE}/repos/{owner}/{repo}/contents/{file_path}"
            response = await client.get(url, headers=self._headers(), params={"ref": branch})
            if response.status_code == 404 and branch == "main":
                return await self.fetch_file(owner, repo, file_path, branch="master")
            response.raise_for_status()
            data = response.json()

        if data.get("encoding") == "base64":
            raw = base64.b64decode(data["content"])
        else:
            raw = data.get("content", "").encode("utf-8")

        filename = file_path.rsplit("/", 1)[-1]
        parsed = self._parser.parse(filename, file_path, raw)
        parsed.metadata["github_sha"] = data.get("sha")
        parsed.metadata["github_url"] = data.get("html_url")
        return parsed

    async def list_and_fetch_all(
        self,
        repo: str,
        *,
        branch: str = "main",
        path: str = "",
    ) -> list[ParsedDocument]:
        owner, repo_name = self.parse_repo_url(repo)
        file_list = await self.list_files(owner, repo_name, branch=branch, path=path)
        documents = []
        for item in file_list:
            try:
                doc = await self.fetch_file(owner, repo_name, item["path"], branch=branch)
                documents.append(doc)
            except Exception:
                continue
        return documents
