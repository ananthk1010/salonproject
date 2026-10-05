from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"
    mode: Literal["live", "replay"]
    reason: Literal["forced_replay", "no_key", "budget_exhausted"] | None = None
    route: str
    budgetRemainingTokens: int
    policyVersion: str
    version: str


class BranchOut(BaseModel):
    id: str
    name: str
    city: str
    openingHours: list[str]


class CustomerOut(BaseModel):
    id: str
    displayName: str
    branchId: str
    joinedOn: str
    tier: str
    lastSpend: int | None = None


class TaskListItem(BaseModel):
    decisionId: str
    interactionId: str | None
    customerId: str | None
    type: str
    status: str
    createdAt: str


class SampleInteraction(BaseModel):
    id: str
    customerId: str
    branchId: str
    channel: str
    text: str
    receivedAt: str
