import httpx
import pytest

from app.config import Settings
from app.jev.client import JevClient, JevUpstreamError


def _settings(**overrides) -> Settings:
    base = {"jev_base_url": "https://fake-gateway.test/typesafe", "jev_api_key": "test-key"}
    base.update(overrides)
    return Settings(**base)


def _ok_response_body():
    return {
        "model": "typesafe-ai/jev",
        "answers": {
            "intent": {
                "type": "choice", "choice": "book_appointment",
                "probabilities": {"book_appointment": 0.9, "other": 0.1},
                "confidence": 0.8,
            },
            "urgency": {
                "type": "score", "score": 1.0,
                "probabilities": {"0": 0.1, "1": 0.8, "2": 0.05, "3": 0.05},
                "confidence": 0.75,
            },
            "wants_callback": {"type": "noul", "noul": 0.05},
        },
        "usage": {"input_tokens": 1000, "output_tokens": 15},
    }


def test_evaluate_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json=_ok_response_body())

    client = JevClient(_settings(), transport=httpx.MockTransport(handler))
    result = client.evaluate({"customer": {}, "branch": {}, "interaction": {}})
    assert result.mode == "live"
    assert result.intent_choice() == "book_appointment"
    assert result.answers["intent"].confidence == 0.8
    assert result.answers["intent"].confidence_is_fallback is False
    assert result.usage.input_tokens == 1000


def test_evaluate_computes_confidence_when_gateway_omits_it():
    body = _ok_response_body()
    del body["answers"]["intent"]["confidence"]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    client = JevClient(_settings(), transport=httpx.MockTransport(handler))
    result = client.evaluate({})
    assert result.answers["intent"].confidence_is_fallback is True
    assert 0.0 <= result.answers["intent"].confidence <= 1.0


def test_evaluate_without_api_key_raises_immediately():
    client = JevClient(_settings(jev_api_key=None))
    with pytest.raises(JevUpstreamError):
        client.evaluate({})


def test_evaluate_401_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "invalid key", "error_type": "invalid_request"})

    client = JevClient(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(JevUpstreamError):
        client.evaluate({})


def test_evaluate_422_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "bad question shape", "error_type": "invalid_request"})

    client = JevClient(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(JevUpstreamError):
        client.evaluate({})


def test_evaluate_429_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(429, json={"message": "rate limited"})
        return httpx.Response(200, json=_ok_response_body())

    client = JevClient(_settings(), transport=httpx.MockTransport(handler))
    result = client.evaluate({})
    assert result.mode == "live"
    assert calls["n"] == 2


def test_evaluate_529_exhausts_retries_and_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(529, json={"message": "overloaded"})

    client = JevClient(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(JevUpstreamError):
        client.evaluate({})
