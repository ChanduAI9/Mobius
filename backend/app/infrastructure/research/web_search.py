import httpx

from app.config import settings
from app.domain.research import SearchResult


class WebSearchService:
    """Multi-provider web search: Tavily (preferred) with DuckDuckGo fallback."""

    async def search(self, query: str, *, max_results: int = 8) -> list[SearchResult]:
        if settings.tavily_api_key:
            results = await self._search_tavily(query, max_results)
            if results:
                return results
        return await self._search_duckduckgo(query, max_results)

    async def _search_tavily(self, query: str, max_results: int) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
            if response.status_code != 200:
                return []
            data = response.json()
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("content", "")[:500],
                    source="tavily",
                )
                for r in data.get("results", [])
            ]

    async def _search_duckduckgo(self, query: str, max_results: int) -> list[SearchResult]:
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(
                        SearchResult(
                            title=r.get("title", ""),
                            url=r.get("href", r.get("link", "")),
                            snippet=r.get("body", r.get("snippet", ""))[:500],
                            source="duckduckgo",
                        )
                    )
            return results
        except Exception:
            return await self._search_ddg_html(query, max_results)

    async def _search_ddg_html(self, query: str, max_results: int) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "MOBIUS/1.0"},
            )
            if response.status_code != 200:
                return []
        import re

        results = []
        for match in re.finditer(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?class="result__snippet"[^>]*>([^<]+)',
            response.text,
            re.DOTALL,
        ):
            if len(results) >= max_results:
                break
            url, title, snippet = match.groups()
            results.append(SearchResult(title=title.strip(), url=url, snippet=snippet.strip(), source="duckduckgo"))
        return results
