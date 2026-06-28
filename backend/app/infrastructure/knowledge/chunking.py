from app.config import settings
from app.domain.knowledge import TextChunk


class ChunkingService:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self._chunk_size = chunk_size or settings.chunk_size
        self._overlap = chunk_overlap or settings.chunk_overlap

    def chunk_text(
        self,
        text: str,
        *,
        filename: str = "",
        file_path: str = "",
    ) -> list[TextChunk]:
        if not text.strip():
            return []

        chunks: list[TextChunk] = []
        start = 0
        index = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self._chunk_size, text_len)

            if end < text_len:
                break_at = self._find_break_point(text, start, end)
                if break_at > start:
                    end = break_at

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(
                    TextChunk(
                        content=chunk_content,
                        chunk_index=index,
                        metadata={
                            "filename": filename,
                            "file_path": file_path,
                            "char_start": start,
                            "char_end": end,
                        },
                    )
                )
                index += 1

            if end >= text_len:
                break
            start = max(end - self._overlap, start + 1)

        return chunks

    @staticmethod
    def _find_break_point(text: str, start: int, end: int) -> int:
        window = text[start:end]
        for sep in ["\n\n", "\n", ". ", " "]:
            pos = window.rfind(sep)
            if pos > len(window) * 0.5:
                return start + pos + len(sep)
        return end
