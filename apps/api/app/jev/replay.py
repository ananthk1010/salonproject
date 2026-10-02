"""Replay store: serves recorded Jev answers from fixtures instead of calling
the model. Used when no API key is configured, the daily budget is spent,
or the live call fails.

Fixtures are JSON files keyed by a lookup key (normally the interaction id)
plus the current questions hash, so editing a question's wording
automatically invalidates stale fixtures instead of silently serving a
mismatched answer.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.jev.answers import ChoiceAnswer, JevAnswers, NoulAnswer, ScoreAnswer, Usage
from app.jev.questions import questions_hash


class ReplayMiss(Exception):
    """Raised when no fixture matches the requested key and question hash."""


def _parse_answer(raw: dict[str, Any]):
    t = raw["type"]
    if t == "choice":
        return ChoiceAnswer(**raw)
    if t == "score":
        return ScoreAnswer(**raw)
    if t == "noul":
        return NoulAnswer(**raw)
    raise ValueError(f"unknown answer type: {t}")


class ReplayStore:
    def __init__(self, fixtures_dir: Path) -> None:
        self.fixtures_dir = fixtures_dir

    def _path(self, key: str) -> Path:
        return self.fixtures_dir / f"{key}.json"

    def get(self, key: str) -> JevAnswers:
        path = self._path(key)
        if not path.exists():
            raise ReplayMiss(
                f"no replay fixture for '{key}'. Live mode is unavailable right now "
                "-- choose one of the sample messages, which all have fixtures."
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("questions_hash") != questions_hash():
            raise ReplayMiss(
                f"fixture for '{key}' was recorded against an older question set "
                "and is stale. Re-run `make eval` to regenerate fixtures."
            )
        answers = {k: _parse_answer(v) for k, v in raw["answers"].items()}
        return JevAnswers(
            answers=answers,
            usage=Usage(**raw.get("usage", {})),
            mode="replay",
            route=raw.get("route", "fixture"),
            latency_ms=0.0,
        )

    def save(self, key: str, jev_answers: JevAnswers) -> None:
        """Record a live answer as a fixture, e.g. from the eval runner."""
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "questions_hash": questions_hash(),
            "route": jev_answers.route,
            "usage": jev_answers.usage.model_dump(),
            "answers": {k: v.model_dump() for k, v in jev_answers.answers.items()},
        }
        self._path(key).write_text(json.dumps(payload, indent=2), encoding="utf-8")
