from dataclasses import dataclass, field


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = "web"


@dataclass
class Citation:
    index: int
    title: str
    url: str
    snippet: str


@dataclass
class ResearchFinding:
    title: str
    summary: str
    content: str
    citations: list[Citation] = field(default_factory=list)
    category: str = "research"
    tags: list[str] = field(default_factory=list)
