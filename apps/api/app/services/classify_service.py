"""Orchestrates one interaction end to end: build state -> ask Jev (or
replay) -> apply the tier/hours rules and the one policy rule -> persist ->
respond. See architecture doc section 6.1 and call flows CF-1/CF-2/CF-3/CF-4.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.audit.store import AuditStore
from app.config import Settings
from app.jev.answers import ChoiceAnswer, JevAnswers, ScoreAnswer
from app.jev.client import JevClient, JevUpstreamError
from app.jev.questions import questions_payload
from app.jev.replay import ReplayStore
from app.jev.state_builder import assert_no_pii, build_state
from app.policy.route import route
from app.rules.tiers import tier
from app.schemas.classify import ClassifyRequest, ClassifyResponse
from app.seed import SeedData


class InteractionNotFound(Exception):
    pass


class ClassifyService:
    def __init__(
        self,
        settings: Settings,
        seed: SeedData,
        jev_client: JevClient,
        replay_store: ReplayStore,
        audit_store: AuditStore,
    ) -> None:
        self.settings = settings
        self.seed = seed
        self.jev_client = jev_client
        self.replay_store = replay_store
        self.audit_store = audit_store

    def _resolve(self, req: ClassifyRequest):
        if req.interactionId:
            interaction = self.seed.interaction(req.interactionId)
            if interaction is None:
                raise InteractionNotFound(req.interactionId)
            return (
                interaction["customerId"],
                interaction["branchId"],
                interaction["channel"],
                interaction["text"],
                datetime.fromisoformat(interaction["receivedAt"]),
                interaction["id"],
            )
        customer = self.seed.customer(req.customerId) if req.customerId else None
        branch_id = customer["branchId"] if customer else self.seed.branches[0]["id"]
        replay_key = f"adhoc-{uuid.uuid4()}"  # free text never matches a recorded fixture
        return req.customerId, branch_id, req.channel, req.text, datetime.now(UTC), replay_key

    def classify(self, req: ClassifyRequest) -> ClassifyResponse:
        customer_id, branch_id, channel, text, received_at, replay_key = self._resolve(req)

        customer = self.seed.customer(customer_id) if customer_id else None
        visits = self.seed.visits_for(customer_id) if customer_id else []
        customer_tier = tier(customer, visits)
        branch = self.seed.branch(branch_id) or self.seed.branches[0]

        recent_visits = [
            {
                "service_category": self._category_for_service(v["serviceId"]),
                "days_ago": self._days_ago(v["date"]),
                "spend": v["spend"],
            }
            for v in visits[:3]
        ]
        state = build_state(
            customer=customer, tier=customer_tier, recent_visits=recent_visits,
            interaction_text=text, interaction_channel=channel, branch=branch,
        )
        assert_no_pii(state)

        jev_answers = self._get_answers(state, replay_key)

        intent = jev_answers.intent_choice() or "other"
        decision = route(intent, branch, received_at)

        confidence_map = {
            key: ans.confidence
            for key, ans in jev_answers.answers.items()
            if isinstance(ans, (ChoiceAnswer, ScoreAnswer))
        }

        decision_id = self.audit_store.save_decision(
            interaction_id=req.interactionId,
            customer_id=customer_id,
            tier=customer_tier,
            questions_snapshot=questions_payload(),
            answers={k: v.model_dump() for k, v in jev_answers.answers.items()},
            confidence_map=confidence_map,
            policy_version=self.settings.policy_version,
            action=decision.action,
            task=decision.task.model_dump() if decision.task else None,
            latency_ms=jev_answers.latency_ms,
            input_tokens=jev_answers.usage.input_tokens,
            output_tokens=jev_answers.usage.output_tokens,
            mode=jev_answers.mode,
            route=jev_answers.route,
        )

        return ClassifyResponse(
            decisionId=decision_id,
            interactionId=req.interactionId,
            customerId=customer_id,
            tier=customer_tier,
            answers=jev_answers.answers,
            confidenceMap=confidence_map,
            action=decision.action,
            task=decision.task,
            policyVersion=self.settings.policy_version,
            mode=jev_answers.mode,
            route=jev_answers.route,
            latencyMs=jev_answers.latency_ms,
            inputTokens=jev_answers.usage.input_tokens,
        )

    def _get_answers(self, state: dict, replay_key: str) -> JevAnswers:
        force_replay = self.settings.jev_mode == "replay"
        have_key = bool(self.settings.jev_api_key)
        under_budget = self.audit_store.daily_tokens_used() < self.settings.daily_budget_tokens
        allow_live = (not force_replay) and self.settings.jev_mode in ("auto", "live") and have_key and under_budget

        if allow_live:
            try:
                return self.jev_client.evaluate(state)
            except JevUpstreamError:
                if self.settings.jev_mode == "live":
                    raise
                # auto mode: fall back to replay on any live failure
        return self.replay_store.get(replay_key)

    def _category_for_service(self, service_id: str) -> str | None:
        for s in self.seed.services:
            if s["id"] == service_id:
                return s["categoryId"]
        return None

    @staticmethod
    def _days_ago(iso_date: str) -> int:
        d = datetime.fromisoformat(iso_date)
        now = datetime.now(d.tzinfo or UTC)
        return max(0, (now - d).days)
