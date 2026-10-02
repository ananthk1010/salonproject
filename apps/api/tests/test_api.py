"""Contract-level tests against the real FastAPI app, running fully in
replay mode against the generated fixtures -- no network access, no key."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_MODE", "replay")
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "audit.db"))
    from app.config import get_settings
    from app.deps import get_audit_store, get_classify_service, get_jev_client, get_replay_store
    get_settings.cache_clear()
    get_audit_store.cache_clear()
    get_classify_service.cache_clear()
    get_jev_client.cache_clear()
    get_replay_store.cache_clear()

    from app.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["mode"] == "replay"


def test_list_customers_includes_all_tiers(client):
    r = client.get("/api/customers")
    assert r.status_code == 200
    tiers = {c["tier"] for c in r.json()}
    assert tiers == {"new", "copper", "bronze", "silver", "gold"}


def test_list_sample_interactions(client):
    r = client.get("/api/interactions")
    assert r.status_code == 200
    assert len(r.json()) >= 10


def test_classify_booking_within_hours_confirms_and_creates_task(client):
    r = client.post("/api/classify", json={"interactionId": "i_001"})
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "confirmed"
    assert body["task"]["type"] == "booking_request"
    assert body["mode"] == "replay"

    tasks = client.get("/api/tasks").json()
    assert any(t["interactionId"] == "i_001" for t in tasks)


def test_classify_booking_outside_hours_rejects_with_no_task(client):
    r = client.post("/api/classify", json={"interactionId": "i_003"})
    body = r.json()
    assert body["action"] == "rejected_outside_hours"
    assert body["task"] is None


def test_classify_non_booking_intent_is_recorded_only(client):
    r = client.post("/api/classify", json={"interactionId": "i_007"})
    body = r.json()
    assert body["action"] == "recorded"
    assert body["task"] is None
    # all six answers are still present and audited, even though unused by policy
    assert set(body["answers"].keys()) == {
        "intent", "service_category", "urgency", "frustration",
        "wants_specific_stylist", "wants_callback",
    }


def test_classify_unknown_interaction_is_404(client):
    r = client.post("/api/classify", json={"interactionId": "does-not-exist"})
    assert r.status_code == 404


def test_classify_malformed_request_is_422(client):
    r = client.post("/api/classify", json={})
    assert r.status_code == 422


def test_classify_free_text_without_fixture_is_503(client):
    r = client.post("/api/classify", json={
        "customerId": "c_001", "channel": "phone_note", "text": "Some new message with no fixture",
    })
    assert r.status_code == 503
