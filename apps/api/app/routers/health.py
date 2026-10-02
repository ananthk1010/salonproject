from __future__ import annotations

from fastapi import APIRouter, Depends

from app.audit.store import AuditStore
from app.config import Settings, get_settings
from app.deps import get_audit_store
from app.schemas.common import HealthOut

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthOut)
def health(
    settings: Settings = Depends(get_settings),
    audit: AuditStore = Depends(get_audit_store),
) -> HealthOut:
    used = audit.daily_tokens_used()
    remaining = max(0, settings.daily_budget_tokens - used)
    return HealthOut(
        mode=settings.jev_mode,  # type: ignore[arg-type]
        route=settings.jev_base_url if settings.jev_api_key else "replay (no key configured)",
        budgetRemainingTokens=remaining,
        policyVersion=settings.policy_version,
        version=settings.app_version,
    )
