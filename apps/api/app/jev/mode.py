"""The one place that decides whether a request would call Jev live or be
served from recorded replay fixtures.

Both ClassifyService (to pick the data source) and /api/health (to tell the
UI which badge to show) use this, so the badge can never disagree with what
the API actually does. JEV_MODE=auto is a *setting*, not a state: this
function turns the setting plus the current facts into live or replay.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.config import Settings

Mode = Literal["live", "replay"]
ReplayReason = Literal["forced_replay", "no_key", "budget_exhausted"]


@dataclass(frozen=True)
class ModeDecision:
    mode: Mode
    reason: ReplayReason | None  # None when mode is "live"


def resolve_mode(settings: Settings, tokens_used_today: int) -> ModeDecision:
    # Anything other than auto/live (including "replay") means fixtures only.
    if settings.jev_mode not in ("auto", "live"):
        return ModeDecision("replay", "forced_replay")
    if not settings.jev_api_key:
        return ModeDecision("replay", "no_key")
    if tokens_used_today >= settings.daily_budget_tokens:
        return ModeDecision("replay", "budget_exhausted")
    return ModeDecision("live", None)
