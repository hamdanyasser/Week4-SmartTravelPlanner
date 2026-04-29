"""Caching helpers.

The brief calls this out explicitly: `lru_cache` for deterministic and
expensive functions, plus a TTL cache for tool responses where it pays off
(weather for the same city within 10 minutes is the same answer).
"""

from app.cache.ttl import TTLCache

__all__ = ["TTLCache"]
