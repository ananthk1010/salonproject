from app.jev.answers import ChoiceAnswer, JevAnswers, NoulAnswer, Usage
from app.jev.replay import ReplayMiss, ReplayStore


def _sample_answers() -> JevAnswers:
    return JevAnswers(
        answers={
            "intent": ChoiceAnswer(choice="book_appointment", probabilities={"book_appointment": 0.9, "other": 0.1}, confidence=0.8),
            "wants_callback": NoulAnswer(noul=0.1),
        },
        usage=Usage(input_tokens=500, output_tokens=10),
        mode="live",
        route="https://example.test",
        latency_ms=120.0,
    )


def test_round_trip(tmp_path):
    store = ReplayStore(tmp_path)
    store.save("i_test", _sample_answers())
    loaded = store.get("i_test")
    assert loaded.mode == "replay"
    assert loaded.intent_choice() == "book_appointment"
    assert loaded.usage.input_tokens == 500


def test_missing_fixture_raises_replay_miss(tmp_path):
    store = ReplayStore(tmp_path)
    try:
        store.get("does-not-exist")
        assert False, "expected ReplayMiss"
    except ReplayMiss:
        pass


def test_stale_fixture_raises_replay_miss(tmp_path, monkeypatch):
    store = ReplayStore(tmp_path)
    store.save("i_test", _sample_answers())
    # Simulate a changed question set by patching the hash function the
    # replay store checks against.
    import app.jev.replay as replay_module
    monkeypatch.setattr(replay_module, "questions_hash", lambda: "different-hash")
    try:
        store.get("i_test")
        assert False, "expected ReplayMiss for a stale fixture"
    except ReplayMiss:
        pass
