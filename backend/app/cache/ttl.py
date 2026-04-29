"""Tiny in-memory async TTL cache.

We do not pull in `cachetools`/`aiocache` because the surface we need is
small enough that the dependency would cost more to justify than it saves.
This cache is process-local (not Redis) so it is safe and predictable
inside a single FastAPI worker; for multi-worker setups we would swap in
Redis behind the same interface.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Async key-value cache with per-entry expiry.

    Keys are tuples (so they can include input payloads); values are any
    Pydantic-serializable result. The cache is concurrency-safe within one
    event loop: parallel callers waiting on the same key share one upstream
    fetch instead of stampeding the underlying API.
    """

    def __init__(self, ttl_seconds: float, max_entries: int = 256) -> None:
        self._ttl = float(ttl_seconds)
        self._max_entries = int(max_entries)
        self._store: dict[tuple, tuple[float, T]] = {}
        self._inflight: dict[tuple, asyncio.Future[T]] = {}
        self._lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0

    def _evict_if_needed(self) -> None:
        if len(self._store) <= self._max_entries:
            return
        oldest_key = min(self._store, key=lambda k: self._store[k][0])
        self._store.pop(oldest_key, None)

    def peek(self, key: tuple) -> T | None:
        """Return the cached value if still fresh, else None. Does not record stats."""

        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    async def get_or_set(
        self,
        key: tuple,
        factory: Callable[[], Awaitable[T]],
    ) -> T:
        """Return cached value, or call `factory()` to populate it."""

        cached = self.peek(key)
        if cached is not None:
            self.hits += 1
            return cached

        async with self._lock:
            cached = self.peek(key)
            if cached is not None:
                self.hits += 1
                return cached
            inflight = self._inflight.get(key)
            if inflight is None:
                inflight = asyncio.get_running_loop().create_future()
                self._inflight[key] = inflight
                creator = True
            else:
                creator = False

        if not creator:
            return await inflight

        self.misses += 1
        try:
            value = await factory()
        except BaseException as exc:
            inflight.set_exception(exc)
            self._inflight.pop(key, None)
            raise

        self._store[key] = (time.monotonic() + self._ttl, value)
        self._evict_if_needed()
        inflight.set_result(value)
        self._inflight.pop(key, None)
        return value

    def clear(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0
