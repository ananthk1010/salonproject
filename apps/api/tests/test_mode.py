"""resolve_mode decides live vs replay; /api/health must report that result,
not the raw JEV_MODE setting (the bug that left the badge on REPLAY even
with a working key)."""
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.jev.mode import resolve_mode


def _settings(**overrides) -> Settings:
    base = {"jev_mode": "auto", "jev_api_key": "test-key", "daily_budget_tokens": 1000}
    base.update(overrides)
    return Settings(**base)


def test_auto_with_key_and_budget_is_live():
    d = resolve_mode(_settings(), tokens_used_today=0)
    assert d.mode == "live"
    assert d.reason is None


def test_live_setting_with_key_is_live():
    assert resolve_mode(_settings(jev_mode="live"), 0).mode == "live"


def test_forced_replay_wins_even_with_a_key():
    d = resolve_mode(_settings(jev_mode="replay"), 0)
    assert (d.mode, d.reason) == ("replay", "forced_replay")


def test_no_key_is_replay():
    d = resolve_mode(_settings(jev_api_key=None), 0)
    assert (d.mode, d.reason) == ("replay", "no_key")


def test_exhausted_budget_is_replay():
    d = resolve_mode(_settings(), tokens_used_today=1000)
    assert (d.mode, d.reason) == ("replay", "budget_exhausted")


def test_just_under_budget_is_still_live():
    assert resolve_mode(_settings(), tokens_used_today=999).mode == "live"


def test_unknown_mode_value_is_treated_as_replay():
    assert resolve_mode(_settings(jev_mode="banana"), 0).mode == "replay"


@pytest.fixture()
def make_client(tmp_path, monkeypatch):
    def _make(**env: str) -> TestClient:
        monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "audit.db"))
        monkeypatch.delenv("JEV_API_KEY", raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        from app.config import get_settings
        from app.deps import get_audit_store, get_classify_service, get_jev_client, get_replay_store

        for cached in (get_settings, get_audit_store, get_classify_service, get_jev_client, get_replay_store):
            cached.cache_clear()
        from app.main import app

        return TestClient(app)

    return _make


def test_health_reports_live_when_auto_with_a_key(make_client):
    body = make_client(JEV_MODE="auto", JEV_API_KEY="test-key").get("/api/health").json()
    assert body["mode"] == "live"
    assert body["reason"] is None
    assert body["route"].startswith("https://")


def test_health_reports_replay_without_a_key(make_client):
    body = make_client(JEV_MODE="auto").get("/api/health").json()
    assert body["mode"] == "replay"
    assert body["reason"] == "no_key"
    assert body["route"] == "replay fixtures"


def test_health_reports_forced_replay_even_with_a_key(make_client):
    body = make_client(JEV_MODE="replay", JEV_API_KEY="test-key").get("/api/health").json()
    assert (body["mode"], body["reason"]) == ("replay", "forced_replay")
