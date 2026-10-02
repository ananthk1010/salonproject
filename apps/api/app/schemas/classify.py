from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.jev.answers import Answer
from app.policy.route import Action, TaskOut


class ClassifyRequest(BaseModel):
    """Either reference a seeded sample interaction by id, or supply free
    text plus a customer id directly. Exactly one of the two forms."""

    interactionId: str | None = None
    customerId: str | None = None
    channel: Literal["phone_note", "web_form", "whatsapp_mock"] | None = None
    text: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _one_form_only(self) -> ClassifyRequest:
        if self.interactionId:
            return self
        if self.customerId and self.channel and self.text:
            return self
        raise ValueError(
            "provide either interactionId, or all of customerId + channel + text"
        )


class ClassifyResponse(BaseModel):
    decisionId: str
    interactionId: str | None
    customerId: str | None
    tier: str
    answers: dict[str, Answer]
    confidenceMap: dict[str, float]
    action: Action
    task: TaskOut | None
    policyVersion: str
    mode: Literal["live", "replay"]
    route: str
    latencyMs: float
    inputTokens: int
