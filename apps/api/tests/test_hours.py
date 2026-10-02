from datetime import datetime

from app.rules.hours import is_open

BRANCH = {"id": "b_x", "openingHours": ["10:00", "20:00"]}


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 29, hour, minute)


def test_open_at_opening_time():
    assert is_open(BRANCH, _at(10, 0)) is True


def test_open_mid_day():
    assert is_open(BRANCH, _at(14, 30)) is True


def test_closed_at_exactly_closing_time():
    assert is_open(BRANCH, _at(20, 0)) is False


def test_closed_before_opening():
    assert is_open(BRANCH, _at(7, 15)) is False


def test_closed_late_at_night():
    assert is_open(BRANCH, _at(21, 45)) is False


def test_open_one_minute_before_close():
    assert is_open(BRANCH, _at(19, 59)) is True
