"""Generates synthetic seed data, a starter golden set, and matching replay
fixtures so the demo and `make eval` work out of the box with no live Jev
key. Re-run this after changing app/jev/questions.py (the fixtures are
keyed partly by the live questions_hash()).

Usage (from apps/api/):
    python scripts/generate_seed.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.jev.answers import ChoiceAnswer, JevAnswers, NoulAnswer, ScoreAnswer, Usage  # noqa: E402
from app.jev.questions import (  # noqa: E402
    FRUSTRATION_LEVELS,
    INTENT_CRITERIA,
    SERVICE_CATEGORY_CRITERIA,
    URGENCY_LEVELS,
)
from app.jev.replay import ReplayStore  # noqa: E402

SEED_DIR = ROOT / "data" / "seed"
EVAL_DIR = ROOT.parent.parent / "eval"
FIXTURES_DIR = EVAL_DIR / "fixtures"

YEAR = 2026

# ---------------------------------------------------------------- branches
BRANCHES = [
    {"id": "b_lakeview", "name": "Lakeview", "city": "Hyderabad", "openingHours": ["10:00", "20:00"]},
    {"id": "b_techpark", "name": "Tech Park", "city": "Hyderabad", "openingHours": ["10:00", "20:00"]},
    {"id": "b_oldtown", "name": "Old Town", "city": "Hyderabad", "openingHours": ["10:00", "20:00"]},
]

# ------------------------------------------------------------- categories
SERVICE_CATEGORIES = [{"id": k, "description": v} for k, v in SERVICE_CATEGORY_CRITERIA.items() if k != "unclear"]

SERVICES = [
    {"id": "svc_haircut", "categoryId": "hair", "name": "Haircut & Style", "durationMin": 45, "priceBand": "rs_500_1000"},
    {"id": "svc_haircolour", "categoryId": "hair", "name": "Hair Colour", "durationMin": 90, "priceBand": "rs_2000_4000"},
    {"id": "svc_hairspa", "categoryId": "hair", "name": "Hair Spa", "durationMin": 60, "priceBand": "rs_1500_2500"},
    {"id": "svc_keratin", "categoryId": "hair", "name": "Keratin Treatment", "durationMin": 150, "priceBand": "rs_5000_8000"},
    {"id": "svc_facial_classic", "categoryId": "skin", "name": "Classic Facial", "durationMin": 45, "priceBand": "rs_1000_1500"},
    {"id": "svc_facial_korean", "categoryId": "skin", "name": "Korean Glass Facial", "durationMin": 60, "priceBand": "rs_2500_3500"},
    {"id": "svc_cleanup", "categoryId": "skin", "name": "Cleanup", "durationMin": 30, "priceBand": "rs_600_900"},
    {"id": "svc_massage_swedish", "categoryId": "spa_therapy", "name": "Swedish Massage", "durationMin": 60, "priceBand": "rs_2000_3000"},
    {"id": "svc_body_polish", "categoryId": "spa_therapy", "name": "Body Polish", "durationMin": 60, "priceBand": "rs_2500_3500"},
    {"id": "svc_manicure", "categoryId": "nails", "name": "Manicure", "durationMin": 30, "priceBand": "rs_400_700"},
    {"id": "svc_pedicure", "categoryId": "nails", "name": "Pedicure", "durationMin": 45, "priceBand": "rs_500_900"},
    {"id": "svc_nailart", "categoryId": "nails", "name": "Nail Art", "durationMin": 30, "priceBand": "rs_300_800"},
    {"id": "svc_beard", "categoryId": "grooming", "name": "Beard Trim", "durationMin": 20, "priceBand": "rs_150_300"},
    {"id": "svc_mens_haircut", "categoryId": "grooming", "name": "Men's Haircut", "durationMin": 30, "priceBand": "rs_300_500"},
    {"id": "svc_bridal", "categoryId": "bridal", "name": "Bridal Makeup Package", "durationMin": 180, "priceBand": "rs_8000_15000"},
]

# -------------------------------------------------------------- customers
# Spend values are chosen to exercise every tier band, including the exact
# boundaries (1500/1501, 3000/3001, 5000/5001).
CUSTOMERS = [
    {"id": "c_001", "displayName": "Anita R.", "phoneMasked": "9xxxxxxx12", "branchId": "b_lakeview", "joinedOn": f"{YEAR-2}-03-10"},
    {"id": "c_002", "displayName": "Kiran S.", "phoneMasked": "9xxxxxxx34", "branchId": "b_techpark", "joinedOn": f"{YEAR-1}-07-22"},
    {"id": "c_003", "displayName": "Meera P.", "phoneMasked": "9xxxxxxx56", "branchId": "b_oldtown", "joinedOn": f"{YEAR-1}-11-02"},
    {"id": "c_004", "displayName": "Ravi K.", "phoneMasked": "9xxxxxxx78", "branchId": "b_lakeview", "joinedOn": f"{YEAR}-01-15"},
    {"id": "c_005", "displayName": "Divya N.", "phoneMasked": "9xxxxxxx90", "branchId": "b_techpark", "joinedOn": f"{YEAR}-09-20"},
    {"id": "c_006", "displayName": "Suresh B.", "phoneMasked": "9xxxxxxx11", "branchId": "b_oldtown", "joinedOn": f"{YEAR-3}-05-01"},
    {"id": "c_007", "displayName": "Lakshmi V.", "phoneMasked": "9xxxxxxx22", "branchId": "b_lakeview", "joinedOn": f"{YEAR-1}-02-14"},
    {"id": "c_008", "displayName": "Arjun T.", "phoneMasked": "9xxxxxxx33", "branchId": "b_techpark", "joinedOn": f"{YEAR-1}-08-08"},
    {"id": "c_009", "displayName": "Priya M.", "phoneMasked": "9xxxxxxx44", "branchId": "b_oldtown", "joinedOn": f"{YEAR}-02-02"},
    {"id": "c_010", "displayName": "Vikram J.", "phoneMasked": "9xxxxxxx55", "branchId": "b_lakeview", "joinedOn": f"{YEAR-2}-12-25"},
    {"id": "c_011", "displayName": "Sneha D.", "phoneMasked": "9xxxxxxx66", "branchId": "b_techpark", "joinedOn": f"{YEAR-1}-04-18"},
    {"id": "c_012", "displayName": "Farah A.", "phoneMasked": "9xxxxxxx77", "branchId": "b_oldtown", "joinedOn": f"{YEAR}-06-06"},
]
# c_999 is intentionally absent from this list: it is used by one sample
# interaction to demonstrate the "customer record not found" -> tier=new path.

# visits: (customerId, serviceId, stylistId, daysAgo, spend, noShow)
_VISITS_RAW = [
    ("c_001", "svc_haircolour", "st_priya", 21, 6200, False),   # gold
    ("c_002", "svc_facial_korean", "st_ravi", 14, 4200, False),  # silver
    ("c_003", "svc_manicure", "st_divya", 10, 2200, False),      # bronze
    ("c_004", "svc_haircut", "st_priya", 5, 900, False),         # copper
    # c_005 has no visits -> tier "new" via the no-visits path
    ("c_006", "svc_keratin", "st_arjun", 30, 8000, False),       # gold
    ("c_007", "svc_massage_swedish", "st_divya", 7, 3800, False),  # silver
    ("c_008", "svc_cleanup", "st_priya", 3, 1500, False),         # copper (boundary)
    ("c_009", "svc_body_polish", "st_ravi", 12, 1501, False),     # bronze (boundary)
    ("c_010", "svc_facial_classic", "st_arjun", 9, 5000, False),  # silver (boundary)
    ("c_011", "svc_pedicure", "st_divya", 4, 5001, False),        # gold (boundary)
    ("c_012", "svc_bridal", "st_priya", 60, 3000, False),         # bronze (boundary)
]

# -------------------------------------------------------------- utilities
def _iso_days_ago(days: int, hour: int = 12, minute: int = 0) -> str:
    # Fixed reference date so the dataset is reproducible, not wall-clock dependent.
    from datetime import timedelta
    ref = datetime(YEAR, 9, 29, 12, 0, tzinfo=timezone.utc)
    dt = ref - timedelta(days=days)
    return dt.replace(hour=hour, minute=minute).isoformat()


VISITS = [
    {
        "id": f"v_{i:03d}",
        "customerId": cust,
        "serviceId": svc,
        "stylistId": stylist,
        "date": _iso_days_ago(days),
        "spend": spend,
        "noShow": no_show,
    }
    for i, (cust, svc, stylist, days, spend, no_show) in enumerate(_VISITS_RAW, start=1)
]


def _dt(day_offset: int, hour: int, minute: int = 0) -> str:
    from datetime import timedelta
    ref = datetime(YEAR, 9, 29, 0, 0, tzinfo=timezone.utc)
    dt = ref + timedelta(days=day_offset)
    return dt.replace(hour=hour, minute=minute).isoformat()


# ----------------------------------------------------------- interactions
# Each tuple: (id, customerId, branchId, channel, text, receivedAt,
#              intent, category, urgency_idx, frustration_idx, wants_stylist, wants_callback)
_INTERACTIONS_RAW = [
    ("i_001", "c_001", "b_lakeview", "phone_note",
     "Hi, I'd like to book a hair colour appointment this Saturday afternoon.",
     _dt(2, 14, 30), "book_appointment", "hair", 1, 0, False, False),

    ("i_002", "c_004", "b_lakeview", "web_form",
     "Can I get a haircut slot today evening around 6pm?",
     _dt(0, 15, 0), "book_appointment", "hair", 2, 0, False, False),

    ("i_003", "c_002", "b_techpark", "whatsapp_mock",
     "Is it possible to book a facial for tomorrow? Sending this now, sorry it's late.",
     _dt(0, 21, 45), "book_appointment", "skin", 1, 0, False, False),

    ("i_004", "c_999", "b_oldtown", "phone_note",
     "Hello, I'd like to book a pedicure appointment for this afternoon please.",
     _dt(1, 7, 15), "book_appointment", "nails", 1, 0, False, False),

    ("i_005", "c_003", "b_oldtown", "web_form",
     "I need to move my Friday manicure appointment to Monday instead, if possible.",
     _dt(1, 11, 0), "reschedule", "nails", 1, 0, False, False),

    ("i_006", "c_006", "b_oldtown", "phone_note",
     "Please cancel my bridal makeup trial booked for next week, something has come up.",
     _dt(3, 10, 30), "cancel", "bridal", 1, 0, False, False),

    ("i_007", "c_007", "b_lakeview", "web_form",
     "What's the price for a Korean glass facial at your Tech Park branch?",
     _dt(0, 12, 0), "price_enquiry", "skin", 0, 0, False, False),

    ("i_008", "c_010", "b_lakeview", "whatsapp_mock",
     "Do you have any offers on hair spa this month?",
     _dt(0, 16, 20), "price_enquiry", "hair", 0, 0, False, False),

    ("i_009", "c_008", "b_techpark", "phone_note",
     "I'm really unhappy, my last hair colour faded within a week! This is unacceptable.",
     _dt(2, 13, 0), "complaint", "hair", 1, 2, False, False),

    ("i_010", "c_009", "b_oldtown", "web_form",
     "The stylist was 40 minutes late for my appointment yesterday, quite frustrating.",
     _dt(1, 9, 45), "complaint", "unclear", 0, 1, False, False),

    ("i_011", "c_011", "b_techpark", "whatsapp_mock",
     "Just wanted to say the pedicure service last week was lovely, thank you!",
     _dt(5, 18, 0), "feedback", "nails", 0, 0, False, False),

    ("i_012", "c_012", "b_oldtown", "web_form",
     "Loved the bridal package, my makeup lasted the whole wedding day. Thank you so much!",
     _dt(10, 19, 0), "feedback", "bridal", 0, 0, False, False),

    ("i_013", "c_005", "b_techpark", "phone_note",
     "Do you have parking available at the Old Town branch?",
     _dt(0, 11, 30), "other", "unclear", 0, 0, False, False),

    ("i_014", "c_001", "b_lakeview", "whatsapp_mock",
     "Can I book a hair spa this weekend with Priya specifically, if she's available?",
     _dt(0, 17, 0), "book_appointment", "hair", 1, 0, True, False),

    ("i_015", "c_002", "b_techpark", "web_form",
     "I'd like to book a spa package but have a few questions, could someone call me back?",
     _dt(0, 13, 45), "book_appointment", "spa_therapy", 1, 0, False, True),

    ("i_016", "c_004", "b_lakeview", "phone_note",
     "This is the third time my appointment got cancelled last minute, very disappointed in this salon.",
     _dt(4, 16, 0), "complaint", "unclear", 1, 2, False, False),

    ("i_017", "c_007", "b_lakeview", "whatsapp_mock",
     "Hi, can you reschedule my massage booking? Sending this quite late, apologies.",
     _dt(0, 22, 10), "reschedule", "spa_therapy", 1, 0, False, False),

    ("i_018", "c_010", "b_lakeview", "phone_note",
     "hi can i come today",
     _dt(0, 10, 15), "book_appointment", "unclear", 1, 0, False, False),
]

INTERACTIONS = [
    {
        "id": r[0], "customerId": r[1], "branchId": r[2], "channel": r[3],
        "text": r[4], "receivedAt": r[5],
    }
    for r in _INTERACTIONS_RAW
]


def _peaked(labels: list[str], top: str, top_p: float = 0.86) -> dict[str, float]:
    rest = [l for l in labels if l != top]
    each = (1 - top_p) / len(rest) if rest else 0.0
    probs = {l: round(each, 4) for l in rest}
    probs[top] = round(1 - sum(probs.values()), 4)
    return probs


def _score_probs(levels: int, idx: float, top_p: float = 0.8) -> dict[str, float]:
    keys = [str(i) for i in range(levels)]
    rest_each = (1 - top_p) / (levels - 1) if levels > 1 else 0.0
    probs = {k: round(rest_each, 4) for k in keys}
    probs[str(int(idx))] = round(1 - rest_each * (levels - 1), 4)
    return probs


def build_fixture(row: tuple) -> JevAnswers:
    (_id, _cust, _branch, _chan, text, _recv, intent, category, urg_idx, frus_idx, stylist, callback) = row

    intent_probs = _peaked(list(INTENT_CRITERIA.keys()), intent)
    category_probs = _peaked(list(SERVICE_CATEGORY_CRITERIA.keys()), category, top_p=0.78)
    urgency_probs = _score_probs(len(URGENCY_LEVELS), urg_idx)
    frustration_probs = _score_probs(len(FRUSTRATION_LEVELS), frus_idx)

    answers = {
        "intent": ChoiceAnswer(choice=intent, probabilities=intent_probs, confidence=0.0),
        "service_category": ChoiceAnswer(choice=category, probabilities=category_probs, confidence=0.0),
        "urgency": ScoreAnswer(score=float(urg_idx), probabilities=urgency_probs, confidence=0.0),
        "frustration": ScoreAnswer(score=float(frus_idx), probabilities=frustration_probs, confidence=0.0),
        "wants_specific_stylist": NoulAnswer(noul=0.9 if stylist else 0.04),
        "wants_callback": NoulAnswer(noul=0.9 if callback else 0.04),
    }
    # fill in confidence from the probabilities, same formula the live client uses
    from app.jev.answers import confidence_from_probabilities
    answers["intent"].confidence = confidence_from_probabilities(intent_probs)
    answers["service_category"].confidence = confidence_from_probabilities(category_probs)
    answers["urgency"].confidence = confidence_from_probabilities(urgency_probs)
    answers["frustration"].confidence = confidence_from_probabilities(frustration_probs)

    approx_tokens = 60 + len(text.split()) * 2 + 900  # rough: state + 6 questions
    return JevAnswers(
        answers=answers,
        usage=Usage(input_tokens=approx_tokens, output_tokens=18),
        mode="replay",
        route="fixture",
        latency_ms=0.0,
    )


def main() -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    (SEED_DIR / "branches.json").write_text(json.dumps(BRANCHES, indent=2), encoding="utf-8")
    (SEED_DIR / "service_categories.json").write_text(json.dumps(SERVICE_CATEGORIES, indent=2), encoding="utf-8")
    (SEED_DIR / "services.json").write_text(json.dumps(SERVICES, indent=2), encoding="utf-8")
    (SEED_DIR / "customers.json").write_text(json.dumps(CUSTOMERS, indent=2), encoding="utf-8")
    (SEED_DIR / "visits.json").write_text(json.dumps(VISITS, indent=2), encoding="utf-8")
    (SEED_DIR / "interactions.json").write_text(json.dumps(INTERACTIONS, indent=2), encoding="utf-8")
    print(f"wrote seed data to {SEED_DIR}")

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    store = ReplayStore(FIXTURES_DIR)

    golden_lines = []
    for row in _INTERACTIONS_RAW:
        (iid, cust, branch, chan, text, recv, intent, category, urg_idx, frus_idx, stylist, callback) = row
        fixture = build_fixture(row)
        store.save(iid, fixture)
        golden_lines.append(json.dumps({
            "id": iid, "customerId": cust, "branchId": branch, "channel": chan,
            "text": text, "receivedAt": recv,
            "label": {
                "intent": intent, "service_category": category,
                "urgency": urg_idx, "frustration": frus_idx,
                "wants_specific_stylist": stylist, "wants_callback": callback,
            },
        }))
    (EVAL_DIR / "golden.jsonl").write_text("\n".join(golden_lines) + "\n", encoding="utf-8")
    print(f"wrote {len(golden_lines)} fixtures + golden.jsonl entries to {EVAL_DIR}")
    print(
        "NOTE: this is a starter set of 18 hand-authored messages. "
        "docs/PHASE1_PLAN.md section 7 calls for 120 for the real evaluation (milestone M3)."
    )


if __name__ == "__main__":
    main()
