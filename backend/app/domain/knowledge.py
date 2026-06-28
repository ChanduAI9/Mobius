import hashlib
import re
from dataclasses import dataclass, field
from enum import StrEnum


class SourceType(StrEnum):
    LOCAL_FOLDER = "local_folder"
    GITHUB = "github"
    UPLOAD = "upload"
    NOTION = "notion"
    GOOGLE_DRIVE = "google_drive"


class IngestionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(StrEnum):
    CONVERSATION = "conversation"
    CODING = "coding"
    ARCHITECTURE = "architecture"
    RESEARCH = "research"


@dataclass
class ParsedDocument:
    filename: str
    file_path: str
    mime_type: str
    content: str
    content_hash: str
    file_size: int
    metadata: dict = field(default_factory=dict)


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievalResult:
    chunk_id: str
    document_id: str
    space_id: str
    content: str
    filename: str
    file_path: str
    score: float
    metadata: dict = field(default_factory=dict)


SUPPORTED_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".rst",
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt",
    ".json", ".yaml", ".yml", ".toml", ".sql", ".html", ".css", ".scss",
    ".pdf", ".docx",
}

IGNORE_PATTERNS = [
    r"node_modules",
    r"\.git",
    r"__pycache__",
    r"\.venv",
    r"venv",
    r"dist/",
    r"build/",
    r"\.next",
    r"\.pytest_cache",
    r"\.egg-info",
    r"package-lock\.json",
    r"yarn\.lock",
]


def should_ignore_path(path: str) -> bool:
    return any(re.search(p, path) for p in IGNORE_PATTERNS)


def compute_content_hash(content: bytes | str) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()
