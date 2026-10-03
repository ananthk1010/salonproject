"""The six typed questions ABC-Salon asks Jev, and nothing else.

Single source of truth: the Pydantic models here define both the wire
format sent to TypeSafe's systemone endpoint and the shape of the answers
we expect back. See docs/ABC-Salon_Architecture_Design.docx section 6.2.

Only `intent` is read by the policy engine (app/policy/route.py). The other
five are computed, shown in the decision panel, and stored in the audit
trail purely to demonstrate Jev's typed-decision output; Phase 1 does not
act on them. There is no `mentions_medical` question in Phase 1 (removed
2026-09-30 at the owner's request -- it did not map to a salon context).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

QuestionType = Literal["choice", "score", "noul"]


class ChoiceQuestion(BaseModel):
    type: Literal["choice"] = "choice"
    instructions: str
    criteria: dict[str, str]


class ScoreQuestion(BaseModel):
    type: Literal["score"] = "score"
    instructions: str
    criteria: list[str]


class NoulQuestion(BaseModel):
    type: Literal["noul"] = "noul"
    instructions: str
    criteria: dict[str, str] | None = None


Question = ChoiceQuestion | ScoreQuestion | NoulQuestion

INTENT_CRITERIA = {
    "book_appointment": "Wants to schedule a salon visit",
    "reschedule": "Wants to move a confirmed booking to a different time",
    "cancel": "Wants to cancel a confirmed booking",
    "price_enquiry": "Asking about prices, offers, or cost of a service",
    "complaint": "Expressing dissatisfaction with a past visit or a service",
    "feedback": "Giving feedback or a compliment, not asking for any action",
    "other": "Does not fit any of the above",
}

SERVICE_CATEGORY_CRITERIA = {
    "hair": "Haircut, Hair-Color, Hair-styling, Hair spa, Keratin or similar hair services",
    "skin": "Facials, skin treatments, cleanups",
    "spa_therapy": "Body massage, spa packages, body treatments",
    "nails": "Manicure, pedicure, nail-polish",
    "grooming": "Men's grooming, beard or shave services",
    "bridal": "Bridal or event makeup and styling packages",
    "unclear": "The message does not specify or imply a service category",
}

URGENCY_LEVELS = [
    "No time pressure; a general or future enquiry",
    "Would like it soon, within the next few days",
    "Fairly urgent, ideally today or tomorrow",
    "Needs action today; explicitly time-sensitive",
]

FRUSTRATION_LEVELS = [
    "Calm, neutral, just stating facts",
    "Frustrated but civil",
    "Very angry or upset",
]

QUESTIONS: dict[str, Question] = {
    "intent": ChoiceQuestion(
        instructions="What is the customer asking for in this message?",
        criteria=INTENT_CRITERIA,
    ),
    "service_category": ChoiceQuestion(
        instructions="Which service family is this message about, if any?",
        criteria=SERVICE_CATEGORY_CRITERIA,
    ),
    "urgency": ScoreQuestion(
        instructions="How time-sensitive is this request?",
        criteria=URGENCY_LEVELS,
    ),
    "frustration": ScoreQuestion(
        instructions="How frustrated or upset does the customer sound?",
        criteria=FRUSTRATION_LEVELS,
    ),
    "wants_specific_stylist": NoulQuestion(
        instructions="The customer asks for a named or specific stylist.",
    ),
    "wants_callback": NoulQuestion(
        instructions="The customer asks to be called back.",
    ),
}

# The policy engine only ever reads this one answer. Keeping it named and
# exported makes that dependency explicit and greppable.
POLICY_RELEVANT_QUESTION = "intent"


def questions_payload() -> dict[str, dict]:
    """Serialise QUESTIONS to the exact JSON shape TypeSafe's systemone expects."""
    return {key: q.model_dump(exclude_none=True) for key, q in QUESTIONS.items()}


def questions_hash() -> str:
    """A short, stable hash of the current question set, used to key replay fixtures
    so that editing a question's wording invalidates stale fixtures automatically."""
    import hashlib
    import json

    blob = json.dumps(questions_payload(), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:12]
