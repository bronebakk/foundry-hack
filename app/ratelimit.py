"""Lightweight in-memory rate limiter (A06 / LLM10 — unbounded LLM consumption).

Generation endpoints call an open-weight model; without a cap they are a cost / denial-of-service
lever (anonymous, too, when ``DEMO_AUTH`` is off). This is a per-key fixed-window limiter — in
memory and per-process, which is fine for the single-worker demo; a production multi-worker
deployment would back this with a shared store (e.g. Redis).
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

_HITS: dict[str, deque] = defaultdict(deque)

# Generous defaults: never trips in normal demo use; bounds abuse.
DEFAULT_LIMIT = 30
DEFAULT_WINDOW = 60.0


def allow(key: str, limit: int = DEFAULT_LIMIT, window: float = DEFAULT_WINDOW) -> bool:
    """Record a hit for ``key`` and return True if it is within ``limit`` per ``window`` seconds."""
    now = time.monotonic()
    q = _HITS[key]
    while q and q[0] <= now - window:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True


def reset() -> None:
    """Clear all counters (used by tests)."""
    _HITS.clear()
