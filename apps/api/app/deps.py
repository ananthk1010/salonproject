"""Dependency wiring for FastAPI. Simple module-level singletons via
lru_cache -- Phase 1 has no need for a heavier DI framework."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.audit.store import AuditStore
from app.config import get_settings
from app.jev.client import JevClient
from app.jev.replay import ReplayStore
from app.seed import get_seed_data
from app.services.classify_service import ClassifyService


@lru_cache
def get_jev_client() -> JevClient:
    return JevClient(get_settings())


@lru_cache
def get_replay_store() -> ReplayStore:
    return ReplayStore(Path(get_settings().fixtures_dir))


@lru_cache
def get_audit_store() -> AuditStore:
    return AuditStore(get_settings().audit_db_path)


@lru_cache
def get_classify_service() -> ClassifyService:
    return ClassifyService(
        settings=get_settings(),
        seed=get_seed_data(),
        jev_client=get_jev_client(),
        replay_store=get_replay_store(),
        audit_store=get_audit_store(),
    )
