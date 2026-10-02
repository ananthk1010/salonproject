"""Typed answers returned by Jev, and the envelope we store/return."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ChoiceAnswer(BaseModel):
    type: Literal["choice"] = "choice"
    choice: str
    probabilities: dict[str, float]
    confidence: float
    confidence_is_fallback: bool = False


class ScoreAnswer(BaseModel):
    type: Literal["score"] = "score"
    score: float
    probabilities: dict[str, float]
    confidence: float
    confidence_is_fallback: bool = False


class NoulAnswer(BaseModel):
    type: Literal["noul"] = "noul"
    noul: float


Answer = ChoiceAnswer | ScoreAnswer | NoulAnswer


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class JevAnswers(BaseModel):
    answers: dict[str, Answer]
    usage: Usage
    mode: Literal["live", "replay"]
    route: str
    latency_ms: float

    def intent_choice(self) -> str | None:
        ans = self.answers.get("intent")
        if isinstance(ans, ChoiceAnswer):
            return ans.choice
        return None


def confidence_from_probabilities(probabilities: dict[str, float]) -> float:
    """Fallback confidence computation when the gateway omits it.

    TypeSafe's published definition collapses the probability distribution's
    shape into a single 0-1 peakedness statistic. For n options with top
    probability p, this generalises their documented 3-option example
    ((3p - 1) / 2) to (n*p - 1) / (n - 1) for n >= 2.
    """
    n = len(probabilities)
    if n <= 1:
        return 1.0
    p_max = max(probabilities.values())
    conf = (n * p_max - 1) / (n - 1)
    return max(0.0, min(1.0, conf))
