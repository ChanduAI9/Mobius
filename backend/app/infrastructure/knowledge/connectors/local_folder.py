import os
from pathlib import Path

from app.domain.knowledge import SUPPORTED_EXTENSIONS, ParsedDocument, should_ignore_path
from app.infrastructure.knowledge.parsers import DocumentParser


class LocalFolderConnector:
    def __init__(self, parser: DocumentParser | None = None) -> None:
        self._parser = parser or DocumentParser()

    def list_files(self, root_path: str, *, extensions: set[str] | None = None) -> list[str]:
        root = Path(root_path).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Path does not exist or is not a directory: {root_path}")

        exts = extensions or SUPPORTED_EXTENSIONS
        files: list[str] = []

        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root)
            if rel_dir == ".":
                rel_dir = ""

            dirnames[:] = [
                d for d in dirnames
                if not should_ignore_path(os.path.join(rel_dir, d))
            ]

            for fname in filenames:
                rel_path = os.path.join(rel_dir, fname) if rel_dir else fname
                if should_ignore_path(rel_path):
                    continue
                ext = f".{fname.rsplit('.', 1)[-1].lower()}" if "." in fname else ""
                if ext in exts:
                    files.append(str(root / rel_path))

        return sorted(files)

    def read_file(self, absolute_path: str) -> ParsedDocument:
        path = Path(absolute_path)
        if not path.exists():
            raise FileNotFoundError(absolute_path)

        data = path.read_bytes()
        rel_path = path.name
        return self._parser.parse(path.name, rel_path, data)

    def read_file_at_root(self, root_path: str, relative_path: str) -> ParsedDocument:
        abs_path = Path(root_path).resolve() / relative_path
        data = abs_path.read_bytes()
        return self._parser.parse(abs_path.name, relative_path.replace("\\", "/"), data)

    @staticmethod
    def get_file_mtime(absolute_path: str) -> float:
        return Path(absolute_path).stat().st_mtime
