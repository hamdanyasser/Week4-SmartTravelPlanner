"""Markdown loading and chunking for the RAG knowledge base."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


RAG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = RAG_DIR.parents[2]
DEFAULT_KNOWLEDGE_ROOT = PROJECT_ROOT / "data" / "knowledge"
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class SourceDocument:
    """One markdown source document after parsing frontmatter."""

    path: Path
    destination: str
    source_title: str
    source_type: str
    content: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChunkedDocument:
    """One chunk ready to embed and store."""

    destination: str
    source_title: str
    source_type: str
    source_path: str
    chunk_index: int
    content: str
    content_hash: str

    @property
    def text_for_embedding(self) -> str:
        """Include metadata in embeddings so destination-name queries work."""

        return " ".join(
            [
                self.destination,
                self.source_title,
                self.source_type,
                self.content,
            ]
        )


def _parse_frontmatter(raw_text: str, path: Path) -> tuple[dict[str, str], str]:
    """Parse a tiny YAML-like frontmatter block.

    We keep this simple on purpose so Day 2 does not need a YAML dependency.
    Supported syntax is `key: value` between the first two `---` lines.
    """

    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Missing frontmatter in {path}")

    metadata: dict[str, str] = {}
    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    if end_index is None:
        raise ValueError(f"Unclosed frontmatter in {path}")

    content = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, content


def load_markdown_document(path: Path) -> SourceDocument:
    """Load one markdown file and validate required metadata."""

    raw_text = path.read_text(encoding="utf-8")
    metadata, content = _parse_frontmatter(raw_text, path)
    required = {"destination", "source_title", "source_type"}
    missing = required - set(metadata)
    if missing:
        raise ValueError(f"{path} is missing metadata keys: {sorted(missing)}")
    if not content:
        raise ValueError(f"{path} has no markdown body content.")
    return SourceDocument(
        path=path,
        destination=metadata["destination"],
        source_title=metadata["source_title"],
        source_type=metadata["source_type"],
        content=content,
    )


def iter_markdown_documents(root: Path = DEFAULT_KNOWLEDGE_ROOT) -> list[SourceDocument]:
    """Return all knowledge documents in stable path order."""

    if not root.exists():
        raise FileNotFoundError(f"Knowledge root does not exist: {root}")
    return [
        load_markdown_document(path)
        for path in sorted(root.rglob("*.md"))
        if path.is_file()
    ]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping character chunks.

    Character chunking is enough for Day 2 because our source docs are short
    and structured. The overlap preserves context when a sentence crosses a
    chunk boundary.
    """

    normalized = " ".join(text.split())
    if len(normalized) <= chunk_size:
        return [normalized]
    if overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start + chunk_size // 2, end)
            if boundary != -1:
                end = boundary
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_document(
    document: SourceDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkedDocument]:
    """Chunk one parsed source document."""

    chunks = chunk_text(document.content, chunk_size=chunk_size, overlap=overlap)
    relative_path = document.path.relative_to(PROJECT_ROOT).as_posix()
    return [
        ChunkedDocument(
            destination=document.destination,
            source_title=document.source_title,
            source_type=document.source_type,
            source_path=relative_path,
            chunk_index=index,
            content=content,
            content_hash=document.content_hash,
        )
        for index, content in enumerate(chunks)
    ]


def build_chunks(root: Path = DEFAULT_KNOWLEDGE_ROOT) -> list[ChunkedDocument]:
    """Load and chunk the entire knowledge base."""

    chunked: list[ChunkedDocument] = []
    for document in iter_markdown_documents(root):
        chunked.extend(chunk_document(document))
    return chunked
