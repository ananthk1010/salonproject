"""Branch opening-hours check -- a fact, not a judgement (see architecture
doc section 6.4). "Booking time" is the time the interaction arrives, not
a customer-requested slot; Phase 1 has no calendar or slot concept.
"""
from __future__ import annotations

from datetime import datetime, time


def is_open(branch: dict, received_at: datetime) -> bool:
    """branch["openingHours"] is ["HH:MM", "HH:MM"] (open, close), e.g.
    ["10:00", "20:00"]. The close time is exclusive-of-after: a message at
    exactly closing time is treated as outside hours."""
    open_str, close_str = branch["openingHours"]
    open_t = time.fromisoformat(open_str)
    close_t = time.fromisoformat(close_str)
    now_t = received_at.time()
    return open_t <= now_t < close_t
