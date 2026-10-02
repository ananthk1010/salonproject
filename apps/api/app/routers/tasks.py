from __future__ import annotations

from fastapi import APIRouter, Depends

from app.audit.store import AuditStore
from app.deps import get_audit_store
from app.schemas.common import TaskListItem

router = APIRouter(tags=["tasks"])


@router.get("/api/tasks", response_model=list[TaskListItem])
def list_tasks(audit: AuditStore = Depends(get_audit_store)) -> list[TaskListItem]:
    """The confirmed-booking board. Phase 1 has exactly one task type and
    one status -- see docs/ABC-Salon_Architecture_Design.docx section 8."""
    return [TaskListItem(**t) for t in audit.list_confirmed_tasks()]


@router.get("/api/export/decisions")
def export_decisions(audit: AuditStore = Depends(get_audit_store)) -> list[dict]:
    """Used by `make eval` to read the audit trail without touching the
    live database file directly (the Render disk is ephemeral anyway)."""
    return audit.export_json()
