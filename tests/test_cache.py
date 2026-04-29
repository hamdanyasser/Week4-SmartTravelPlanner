"""TTLCache: hit/miss, expiry, single-flight stampede protection."""

from __future__ import annotations

import asyncio

import pytest

from app.cache import TTLCache


@pytest.mark.asyncio
async def test_get_or_set_caches_value():
    cache = TTLCache[int](ttl_seconds=60.0)
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        return 42

    assert await cache.get_or_set(("k",), factory) == 42
    assert await cache.get_or_set(("k",), factory) == 42
    assert calls == 1
    assert cache.hits == 1
    assert cache.misses == 1


@pytest.mark.asyncio
async def test_ttl_expiry_triggers_refetch():
    cache = TTLCache[int](ttl_seconds=0.05)
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        return calls

    first = await cache.get_or_set(("k",), factory)
    await asyncio.sleep(0.1)
    second = await cache.get_or_set(("k",), factory)
    assert first == 1
    assert second == 2


@pytest.mark.asyncio
async def test_concurrent_callers_share_one_factory_call():
    """Two parallel `get_or_set` for the same key must not double-fetch."""

    cache = TTLCache[int](ttl_seconds=60.0)
    calls = 0

    async def factory() -> int:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.02)
        return 7

    a, b = await asyncio.gather(
        cache.get_or_set(("k",), factory),
        cache.get_or_set(("k",), factory),
    )
    assert a == b == 7
    assert calls == 1


@pytest.mark.asyncio
async def test_eviction_when_over_capacity():
    cache = TTLCache[int](ttl_seconds=60.0, max_entries=2)

    async def factory(value):
        async def inner() -> int:
            return value

        return inner

    await cache.get_or_set(("a",), await factory(1))
    await cache.get_or_set(("b",), await factory(2))
    await cache.get_or_set(("c",), await factory(3))
    # One of the older entries must have been evicted.
    assert len(cache._store) == 2
