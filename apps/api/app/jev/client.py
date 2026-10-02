"""Thin HTTP client for Jev, called through Vercel AI Gateway's
TypeSafe-compatible endpoint (docs/PHASE1_PLAN.md section 2.2).

Deliberately not the `typesafe-sdk` Python package: that SDK has no
documented way to override its base URL, and the request/response shape
here is simple enough (one POST, one JSON body) that a ~40-line httpx
client is both less code and more portable -- switching to TypeSafe direct,
or to Cloudflare's native endpoint, is a config change, not a rewrite.
"""
from __future__ import annotations

import time

import httpx

from app.config import Settings
from app.jev.answers import (
    ChoiceAnswer,
    JevAnswers,
    NoulAnswer,
    ScoreAnswer,
    Usage,
    confidence_from_probabilities,
)
from app.jev.questions import questions_payload

RETRYABLE_STATUS = {429, 529}
MAX_ATTEMPTS = 3
BACKOFF_BASE_S = 0.5


class JevUpstreamError(Exception):
    """The live call failed after retries (or failed in a non-retryable way)."""


def _parse_answers(raw: dict) -> dict:
    out = {}
    for key, a in raw.items():
        t = a.get("type")
        if t == "choice":
            conf = a.get("confidence")
            fallback = conf is None
            if fallback:
                conf = confidence_from_probabilities(a["probabilities"])
            out[key] = ChoiceAnswer(
                choice=a["choice"], probabilities=a["probabilities"],
                confidence=conf, confidence_is_fallback=fallback,
            )
        elif t == "score":
            conf = a.get("confidence")
            fallback = conf is None
            if fallback:
                conf = confidence_from_probabilities(a["probabilities"])
            out[key] = ScoreAnswer(
                score=a["score"], probabilities=a["probabilities"],
                confidence=conf, confidence_is_fallback=fallback,
            )
        elif t == "noul":
            out[key] = NoulAnswer(noul=a["noul"])
        else:
            raise ValueError(f"unknown answer type from gateway: {t!r}")
    return out


class JevClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.jev_base_url,
            timeout=20.0,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def evaluate(self, state: dict) -> JevAnswers:
        """Call POST /v1/systemone with the fixed question set and the given
        state. Raises JevUpstreamError on anything unrecoverable; the caller
        (classify_service) decides whether to fall back to replay."""
        if not self.settings.jev_api_key:
            raise JevUpstreamError("JEV_API_KEY is not set")

        body = {
            "model": self.settings.jev_model,
            "state": state,
            "questions": questions_payload(),
        }
        headers = {"Authorization": f"Bearer {self.settings.jev_api_key}"}

        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.monotonic()
            try:
                resp = self._client.post("/v1/systemone", json=body, headers=headers)
            except httpx.HTTPError as exc:
                last_error = exc
                time.sleep(BACKOFF_BASE_S * attempt)
                continue
            latency_ms = (time.monotonic() - started) * 1000

            if resp.status_code in RETRYABLE_STATUS and attempt < MAX_ATTEMPTS:
                last_error = JevUpstreamError(f"HTTP {resp.status_code}, retrying")
                time.sleep(BACKOFF_BASE_S * attempt)
                continue

            if resp.status_code != 200:
                raise JevUpstreamError(
                    f"gateway returned HTTP {resp.status_code}: {resp.text[:300]}"
                )

            payload = resp.json()
            return JevAnswers(
                answers=_parse_answers(payload["answers"]),
                usage=Usage(**payload.get("usage", {})),
                mode="live",
                route=self.settings.jev_base_url,
                latency_ms=latency_ms,
            )

        raise JevUpstreamError(f"gateway call failed after {MAX_ATTEMPTS} attempts: {last_error}")
