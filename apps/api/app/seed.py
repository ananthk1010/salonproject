"""Loads the JSON seed data into memory at startup. Read-only, in-process --
no database for reference data in Phase 1."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import SEED_DIR


def _load(name: str) -> Any:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


class SeedData:
    def __init__(self) -> None:
        self.branches: list[dict] = _load("branches.json")
        self.service_categories: list[dict] = _load("service_categories.json")
        self.services: list[dict] = _load("services.json")
        self.customers: list[dict] = _load("customers.json")
        self.visits: list[dict] = _load("visits.json")
        self.interactions: list[dict] = _load("interactions.json")

        self._branches_by_id = {b["id"]: b for b in self.branches}
        self._customers_by_id = {c["id"]: c for c in self.customers}
        self._interactions_by_id = {i["id"]: i for i in self.interactions}

    def branch(self, branch_id: str) -> dict | None:
        return self._branches_by_id.get(branch_id)

    def customer(self, customer_id: str) -> dict | None:
        return self._customers_by_id.get(customer_id)

    def interaction(self, interaction_id: str) -> dict | None:
        return self._interactions_by_id.get(interaction_id)

    def visits_for(self, customer_id: str) -> list[dict]:
        """Most-recent-first."""
        rows = [v for v in self.visits if v["customerId"] == customer_id]
        return sorted(rows, key=lambda v: v["date"], reverse=True)


@lru_cache
def get_seed_data() -> SeedData:
    return SeedData()
