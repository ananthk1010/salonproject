from app.rules.tiers import tier, tier_for_spend


def test_no_record_is_new():
    assert tier(None, []) == "new"


def test_record_with_no_visits_is_new():
    assert tier({"id": "c_x"}, []) == "new"


def test_copper_band():
    assert tier_for_spend(0) == "copper"
    assert tier_for_spend(900) == "copper"
    assert tier_for_spend(1500) == "copper"  # boundary


def test_bronze_band():
    assert tier_for_spend(1501) == "bronze"  # boundary
    assert tier_for_spend(2200) == "bronze"
    assert tier_for_spend(3000) == "bronze"  # boundary


def test_silver_band():
    assert tier_for_spend(3001) == "silver"  # boundary
    assert tier_for_spend(4200) == "silver"
    assert tier_for_spend(5000) == "silver"  # boundary


def test_gold_band_is_open_ended():
    assert tier_for_spend(5001) == "gold"  # boundary
    assert tier_for_spend(8000) == "gold"
    assert tier_for_spend(1_000_000) == "gold"  # must not fall through


def test_none_spend_is_new():
    assert tier_for_spend(None) == "new"


def test_tier_uses_most_recent_visit_only():
    visits = [{"spend": 8000}, {"spend": 100}]  # most-recent-first
    assert tier({"id": "c_x"}, visits) == "gold"
