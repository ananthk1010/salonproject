from __future__ import annotations

from fastapi import APIRouter, Depends

from app.audit.store import AuditStore
from app.config import Settings, get_settings
from app.deps import get_audit_store
from app.jev.mode import resolve_mode
from app.schemas.common import HealthOut

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthOut)
def health(
    settings: Settings = Depends(get_settings),
    audit: AuditStore = Depends(get_audit_store),
) -> HealthOut:
    used = audit.daily_tokens_used()
    remaining = max(0, settings.daily_budget_tokens - used)
    # Report the mode actually in effect, not the JEV_MODE setting: "auto"
    # is a setting, and the UI badge needs to know live or replay.
    decision = resolve_mode(settings, used)
    return HealthOut(
        mode=decision.mode,
        reason=decision.reason,
        route=settings.jev_base_url if decision.mode == "live" else "replay fixtures",
        budgetRemainingTokens=remaining,
        policyVersion=settings.policy_version,
        version=settings.app_version,
    )
