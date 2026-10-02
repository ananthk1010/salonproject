"""The entire Phase 1 policy, per the owner's instruction of 2026-09-30:
"keep it simple ... for Policy just have the below: if booking time is
within hours, confirm the booking." See architecture doc section 6.3.

One rule, three possible outcomes. No confidence gates, no priority
formula, no medical override -- all of that was in the v1.0 draft and was
deliberately removed. Policy reads exactly one Jev answer (`intent`) and
one deterministic fact (`is_open`).
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.rules.hours import is_open

Action = Literal["confirmed", "rejected_outside_hours", "recorded"]

BOOKING_INTENT = "book_appointment"


class TaskOut(BaseModel):
    type: Literal["booking_request"] = "booking_request"
    status: Literal["confirmed"] = "confirmed"


class RoutingDecision(BaseModel):
    action: Action
    task: TaskOut | None = None


def route(intent: str, branch: dict, received_at: datetime) -> RoutingDecision:
    if intent != BOOKING_INTENT:
        return RoutingDecision(action="recorded", task=None)
    if is_open(branch, received_at):
        return RoutingDecision(action="confirmed", task=TaskOut())
    return RoutingDecision(action="rejected_outside_hours", task=None)
