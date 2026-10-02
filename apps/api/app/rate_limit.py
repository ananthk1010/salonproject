"""A minimal per-IP rate limiter for the one endpoint that can cost money.
In-memory, single-process -- adequate for a Render Free instance, which is
never horizontally scaled in Phase 1."""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.config import get_settings

_hits: dict[str, list[float]] = defaultdict(list)


def rate_limit(request: Request) -> None:
    limit = get_settings().rate_limit_per_min
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window_start = now - 60
    hits = [t for t in _hits[ip] if t > window_start]
    if len(hits) >= limit:
        raise HTTPException(status_code=429, detail="rate limit exceeded, try again shortly")
    hits.append(now)
    _hits[ip] = hits
