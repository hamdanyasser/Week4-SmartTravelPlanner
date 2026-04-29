"""Embedding providers for retrieval.

Day 2 uses a deterministic local provider so the project can be verified
without external services or secrets. The interface is intentionally small:
anything that can turn text into a list of floats can be swapped in later.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from itertools import pairwise
from typing import Protocol

from app.config import get_settings

DEFAULT_EMBEDDING_DIMENSION = 384
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "best",
    "but",
    "by",
    "can",
    "for",
    "from",
    "good",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "travel",
    "traveler",
    "travelers",
    "trip",
    "with",
}
DOMAIN_STOPWORDS = {
    "destination",
    "fit",
    "july",
    "pressure",
    "reality",
    "recommendation",
    "signals",
}
TOKEN_ALIASES = {
    "beaches": "beach",
    "costs": "cost",
    "crowded": "crowd",
    "crowding": "crowd",
    "hikes": "hike",
    "hiking": "hike",
    "hot": "warm",
    "islands": "island",
    "lesser": "less",
    "low": "less",
    "lower": "less",
    "mountains": "mountain",
    "rainy": "rain",
    "tourism": "tourist",
    "touristy": "tourist",
    "trails": "trail",
    "villages": "village",
    "warmth": "warm",
}
DOMAIN_VOCAB = [
    "adventure",
    "altitude",
    "beach",
    "budget",
    "car",
    "coast",
    "culture",
    "crowd",
    "dry",
    "family",
    "flight",
    "food",
    "forest",
    "hike",
    "island",
    "less",
    "logistics",
    "mountain",
    "rain",
    "rainforest",
    "safe",
    "summer",
    "tourist",
    "trail",
    "transfer",
    "volcano",
    "warm",
    "wildlife",
]
DOMAIN_INDEX = {token: index for index, token in enumerate(DOMAIN_VOCAB)}


class EmbeddingProvider(Protocol):
    """Small interface shared by local and future real embeddings."""

    dimension: int
    name: str

    def embed_text(self, text: str) -> list[float]:
        """Embed one text string."""

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed several text strings."""


def tokenize(text: str) -> list[str]:
    """Lowercase text into stable alphanumeric tokens."""

    tokens: list[str] = []
    for raw_token in TOKEN_RE.findall(text.lower()):
        token = TOKEN_ALIASES.get(raw_token, raw_token)
        if token in STOPWORDS or token in DOMAIN_STOPWORDS:
            continue
        tokens.append(token)
    return tokens


@dataclass(frozen=True)
class DeterministicEmbeddingProvider:
    """Hashing-vector fallback with no network and no secrets.

    It is not a semantic embedding model. It is a deterministic bag-of-words
    vector that makes local retrieval demo-safe and repeatable. Because both
    documents and queries use the same hashing function, lexical overlap still
    ranks relevant destination chunks above unrelated ones. We include adjacent
    token pairs ("warm_island", "budget_hiking") so short queries have a little
    more shape than plain word counts.
    """

    dimension: int = DEFAULT_EMBEDDING_DIMENSION
    name: str = "deterministic-hashing-v1"

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = tokenize(text)
        weighted_terms: list[tuple[str, float]] = [(token, 1.0) for token in tokens]
        weighted_terms.extend(
            (f"{left}_{right}", 1.5) for left, right in pairwise(tokens)
        )

        for term, weight in weighted_terms:
            if term in DOMAIN_INDEX and DOMAIN_INDEX[term] < self.dimension:
                vector[DOMAIN_INDEX[term]] += weight * 1.5
                continue
            digest = hashlib.sha256(term.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            vector[index] += weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


@dataclass(frozen=True)
class ExternalEmbeddingProviderPlaceholder:
    """Placeholder for a future real embedding provider.

    The code path is explicit so adding OpenAI/Ollama/Hugging Face embeddings
    later does not require changing the retriever interface. It intentionally
    raises until we add and test that provider.
    """

    dimension: int = DEFAULT_EMBEDDING_DIMENSION
    name: str = "external-placeholder"

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError(
            "External embeddings are not wired yet. Use EMBEDDING_PROVIDER=deterministic."
        )

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider.

    Day 2 defaults to deterministic embeddings. A real provider can be added
    later behind the same interface once an API key and dependency are chosen.
    """

    settings = get_settings()
    provider = settings.embedding_provider.lower().strip()
    if provider == "deterministic":
        return DeterministicEmbeddingProvider(dimension=settings.embedding_dimension)
    if provider == "openai" and not settings.openai_api_key:
        raise ValueError("EMBEDDING_PROVIDER=openai requires OPENAI_API_KEY.")
    if provider in {"openai", "ollama", "external"}:
        return ExternalEmbeddingProviderPlaceholder(
            dimension=settings.embedding_dimension,
            name=f"{provider}-placeholder",
        )
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}")


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for already-normalized vectors."""

    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimension.")
    return sum(a * b for a, b in zip(left, right, strict=False))
