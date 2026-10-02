import pytest

from app.jev.state_builder import assert_no_pii, build_state

BRANCH = {"id": "b_lakeview", "name": "Lakeview"}


def _state(customer):
    return build_state(
        customer=customer,
        tier="gold",
        recent_visits=[{"service_category": "hair", "days_ago": 5, "spend": 6200}],
        interaction_text="Hello, I'd like a haircut.",
        interaction_channel="phone_note",
        branch=BRANCH,
    )


def test_state_never_contains_customer_name_or_phone():
    customer = {"id": "c_001", "displayName": "Anita R.", "phoneMasked": "9xxxxxxx12"}
    state = _state(customer)
    assert_no_pii(state)  # must not raise
    blob = str(state)
    assert "Anita" not in blob
    assert "9xxxxxxx12" not in blob


def test_state_handles_unknown_customer():
    state = _state(None)
    assert state["customer"]["id"] is None
    assert_no_pii(state)


def test_branch_name_is_allowed_through():
    """Branch display name is not PII and must not trip the guard."""
    state = _state(None)
    assert state["branch"]["name"] == "Lakeview"
    assert_no_pii(state)  # must not raise


def test_assert_no_pii_catches_a_leaked_name_field():
    bad_state = {"customer": {"displayName": "Leaked Name"}}
    with pytest.raises(ValueError):
        assert_no_pii(bad_state)


def test_recent_visits_capped_at_three():
    many_visits = [{"service_category": "hair", "days_ago": i, "spend": 1000} for i in range(5)]
    state = build_state(
        customer=None, tier="gold", recent_visits=many_visits,
        interaction_text="hi", interaction_channel="phone_note", branch=BRANCH,
    )
    assert len(state["customer"]["last_visits"]) == 3
