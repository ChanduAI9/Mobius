import pytest

from app.domain.knowledge import compute_content_hash, should_ignore_path
from app.infrastructure.knowledge.chunking import ChunkingService
from app.infrastructure.knowledge.parsers import DocumentParser


class TestChunkingService:
    def setup_method(self):
        self.chunker = ChunkingService(chunk_size=100, chunk_overlap=20)

    def test_chunk_short_text(self):
        chunks = self.chunker.chunk_text("Hello world", filename="test.txt")
        assert len(chunks) == 1
        assert chunks[0].content == "Hello world"

    def test_chunk_long_text(self):
        text = "word " * 200
        chunks = self.chunker.chunk_text(text, filename="test.txt")
        assert len(chunks) > 1
        assert all(c.chunk_index == i for i, c in enumerate(chunks))

    def test_empty_text(self):
        assert self.chunker.chunk_text("") == []


class TestDocumentParser:
    def setup_method(self):
        self.parser = DocumentParser()

    def test_parse_markdown(self):
        data = b"# Title\n\nSome content here."
        doc = self.parser.parse("readme.md", "readme.md", data)
        assert "Title" in doc.content
        assert doc.mime_type == "text/markdown"
        assert len(doc.content_hash) == 64

    def test_parse_python(self):
        data = b"def hello():\n    return 'world'\n"
        doc = self.parser.parse("main.py", "src/main.py", data)
        assert "def hello" in doc.content
        assert doc.mime_type == "text/x-python"


class TestKnowledgeUtils:
    def test_should_ignore_node_modules(self):
        assert should_ignore_path("src/node_modules/package/index.js")

    def test_should_not_ignore_src(self):
        assert not should_ignore_path("src/main.py")

    def test_content_hash_deterministic(self):
        h1 = compute_content_hash("test content")
        h2 = compute_content_hash("test content")
        assert h1 == h2
        assert h1 != compute_content_hash("different")
