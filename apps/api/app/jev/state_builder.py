"""Builds the `state` object sent to Jev.

Privacy rule (see docs/ABC-Salon_Architecture_Design.docx section 2.3 and
12.2): Jev never receives a customer's display name or phone number. Only
the customer id, tier, a short visit history, the message itself, and
branch context go into the state.
"""
from __future__ import annotations

from typing import Any


def build_state(
    *,
    customer: dict[str, Any] | None,
    tier: str,
    recent_visits: list[dict[str, Any]],
    interaction_text: str,
    interaction_channel: str,
    branch: dict[str, Any],
) -> dict[str, Any]:
    """Build the Jev `state` payload. `customer` may be None for a brand-new,
    unregistered customer -- tier will already be "new" in that case."""
    customer_block: dict[str, Any] = {
        "id": customer["id"] if customer else None,
        "tier": tier,
        "last_visits": [
            {
                "service_category": v.get("service_category"),
                "days_ago": v.get("days_ago"),
                "spend": v.get("spend"),
            }
            for v in recent_visits[:3]
        ],
    }
    return {
        "customer": customer_block,
        "branch": {"id": branch["id"], "name": branch.get("name")},
        "interaction": {"channel": interaction_channel, "text": interaction_text},
    }


_FORBIDDEN_KEYS = {"displayName", "display_name", "phone", "phoneMasked", "phone_masked"}


def assert_no_pii(state: dict[str, Any]) -> None:
    """Defence in depth: raise if anything that looks like a name or phone
    number key ever ends up in a state payload. Used by the unit test and
    cheap enough to also run in the hot path."""

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in _FORBIDDEN_KEYS:
                    raise ValueError(f"PII-looking key '{k}' found in Jev state payload")
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(state)
