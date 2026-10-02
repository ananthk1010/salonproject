from datetime import datetime

from app.policy.route import route

BRANCH = {"id": "b_x", "openingHours": ["10:00", "20:00"]}


def test_booking_within_hours_is_confirmed():
    d = route("book_appointment", BRANCH, datetime(2026, 9, 29, 14, 0))
    assert d.action == "confirmed"
    assert d.task is not None
    assert d.task.type == "booking_request"
    assert d.task.status == "confirmed"


def test_booking_outside_hours_is_rejected_with_no_task():
    d = route("book_appointment", BRANCH, datetime(2026, 9, 29, 21, 40))
    assert d.action == "rejected_outside_hours"
    assert d.task is None


def test_non_booking_intents_are_recorded_with_no_task():
    for intent in ["reschedule", "cancel", "price_enquiry", "complaint", "feedback", "other"]:
        d = route(intent, BRANCH, datetime(2026, 9, 29, 14, 0))
        assert d.action == "recorded", intent
        assert d.task is None, intent


def test_non_booking_intent_outside_hours_is_still_recorded_not_rejected():
    """Rejection is specific to bookings; a complaint at midnight is not
    'rejected', there is simply nothing to confirm or reject about it."""
    d = route("complaint", BRANCH, datetime(2026, 9, 29, 23, 0))
    assert d.action == "recorded"
    assert d.task is None
