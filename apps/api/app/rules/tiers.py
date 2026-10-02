"""Customer tier: a deterministic rule, not a Jev question (owner's decision,
2026-09-30 -- see docs/PHASE1_PLAN.md section 4.1).

    new     no customer record, or a record with no completed visits yet
    copper  last visit spend < Rs 1,500
    bronze  Rs 1,501 -- Rs 3,000
    silver  Rs 3,001 -- Rs 5,000
    gold    Rs 5,001 and above (open-ended)

"Last spend" is the most recent single visit's amount, not a 12-month
total. The gold band is deliberately left open-ended: the owner's original
wording capped it at Rs 10,000, which would leave a bigger spender with no
tier at all.
"""
from __future__ import annotations

from typing import Literal

Tier = Literal["new", "copper", "bronze", "silver", "gold"]


def tier_for_spend(last_spend: float | None) -> Tier:
    """Pure function: last visit spend in rupees -> tier. `None` (no visits
    yet) maps to "new", same as a missing customer record.

    The owner's original wording ("copper: < 1500", "bronze: 1501-3000")
    left a one-rupee gap at exactly 1500. Resolved here by making the
    bands contiguous: copper is <= 1500, bronze starts at 1501."""
    if last_spend is None:
        return "new"
    if last_spend <= 1500:
        return "copper"
    if last_spend <= 3000:
        return "bronze"
    if last_spend <= 5000:
        return "silver"
    return "gold"  # 5001 and above, deliberately open-ended


def tier(customer: dict | None, visits: list[dict]) -> Tier:
    """tier(customer, visits) as named in the architecture doc. `customer`
    is None when no record was found for the given id. `visits` should
    already be sorted most-recent-first; only the first (most recent)
    entry's spend is used."""
    if customer is None:
        return "new"
    if not visits:
        return "new"
    return tier_for_spend(visits[0].get("spend"))
