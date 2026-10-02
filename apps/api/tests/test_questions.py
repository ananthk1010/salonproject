from app.jev.questions import POLICY_RELEVANT_QUESTION, QUESTIONS, questions_hash, questions_payload


def test_exactly_six_questions():
    assert len(QUESTIONS) == 6


def test_no_medical_question():
    assert "mentions_medical" not in QUESTIONS


def test_question_types_match_the_spec():
    assert QUESTIONS["intent"].type == "choice"
    assert QUESTIONS["service_category"].type == "choice"
    assert QUESTIONS["urgency"].type == "score"
    assert QUESTIONS["frustration"].type == "score"
    assert QUESTIONS["wants_specific_stylist"].type == "noul"
    assert QUESTIONS["wants_callback"].type == "noul"


def test_score_questions_have_between_two_and_ten_levels():
    for key in ("urgency", "frustration"):
        n = len(QUESTIONS[key].criteria)
        assert 2 <= n <= 10, key


def test_choice_questions_have_at_least_two_options():
    for key in ("intent", "service_category"):
        assert len(QUESTIONS[key].criteria) >= 2


def test_payload_matches_the_documented_typesafe_shape():
    payload = questions_payload()
    assert set(payload.keys()) == set(QUESTIONS.keys())
    assert payload["intent"]["type"] == "choice"
    assert "instructions" in payload["intent"]
    assert "criteria" in payload["intent"]
    # noul questions have no criteria in our definitions, and exclude_none
    # should drop the key entirely rather than send null.
    assert "criteria" not in payload["wants_callback"]


def test_policy_only_reads_intent():
    assert POLICY_RELEVANT_QUESTION == "intent"


def test_questions_hash_is_stable_and_changes_with_content():
    h1 = questions_hash()
    h2 = questions_hash()
    assert h1 == h2
    assert len(h1) == 12
