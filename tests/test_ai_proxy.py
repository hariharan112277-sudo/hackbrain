"""
AI Gateway Relay Test Suite — Track B (Lathika) — Stage 3 (Testing)
Industrial Operating Brain (IOB) Platform

Validates Part 4 Stage 1 (AI Gateway Client):
  • Each /api/v1/ai/* route relays the request/response body byte-for-byte
    without reshaping any field (Part 2.3's frozen AI contract).
  • Pointing AI_SERVICE_URL at a dead host returns the AI_UNAVAILABLE
    envelope instead of hanging or raising a raw 500.

Isolation:
  ``app.services.ai_client.call_ai`` is monkeypatched per-test so no real
  ai-platform process is required to run this suite.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars-minimum")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ai_proxy.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import ai_proxy
from app.services import ai_client

client = TestClient(app)

# Part 2.3's frozen, real (not placeholder) predictive/infer response shape.
FROZEN_PREDICTIVE_RESPONSE = {
    "success": True,
    "data": {
        "asset_id": "asset-101",
        "component_id": "asset-101-bearing-de",
        "rul": {
            "value_days": 3.8,
            "lower_bound_days": 2.66,
            "upper_bound_days": 4.94,
            "confidence_level": 0.9,
            "model_name": "xgboost_rul_v1",
            "model_version": "1.0.0",
        },
        "failure_probability": {
            "probability": 0.8899,
            "predicted_window": {
                "earliest": "2026-07-05T00:00:00Z",
                "latest": "2026-07-09T00:00:00Z",
                "most_likely": "2026-07-07T00:00:00Z",
            },
            "failure_mode_id": "failuremode-bearing-overheat",
            "failure_mode_label": "Bearing Overheat",
            "model_name": "xgboost_failure_classifier_v1",
            "model_version": "1.0.0",
        },
        "anomaly_flags": [
            {
                "sensor_id": "asset-101-s6",
                "metric": "load_kw",
                "anomaly_score": -0.1088,
                "is_anomalous": True,
                "severity": "CRITICAL",
                "detected_at": "2026-07-05T10:15:32Z",
            }
        ],
        "anomalous_sensors": ["asset-101-s6"],
        "explanation_id": "uuid-linkable-to-/xai/explain",
        "inference_latency_ms": 12.4,
        "generated_at": "2026-07-05T10:15:32Z",
        "fallback_used": False,
    },
    "error": None,
    "request_id": "req-123",
    "generated_at": "2026-07-05T10:15:32Z",
}


@pytest.fixture(autouse=True)
def _clear_override():
    yield
    app.dependency_overrides.clear()


def test_predictive_infer_relays_frozen_shape_byte_for_byte(monkeypatch):
    """POST /api/v1/ai/predictive/infer must return call_ai's body unmodified."""

    captured = {}

    async def fake_call_ai(path, *, payload=None, method="POST"):
        captured["path"] = path
        captured["payload"] = payload
        captured["method"] = method
        return FROZEN_PREDICTIVE_RESPONSE

    monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)

    body = {"asset_id": "asset-101", "component_id": "asset-101-bearing-de"}
    response = client.post("/api/v1/ai/predictive/infer", json=body)

    assert response.status_code == 200
    assert response.json() == FROZEN_PREDICTIVE_RESPONSE
    assert captured["path"] == "/api/v1/predictive/infer"
    assert captured["payload"] == body
    assert captured["method"] == "POST"


def test_predictive_explain_relays_query_and_response(monkeypatch):
    async def fake_call_ai(path, *, payload=None, method="GET"):
        assert path == "/api/v1/xai/explain?asset_id=asset-101"
        return {"success": True, "data": {"asset_id": "asset-101"}}

    monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)

    response = client.get("/api/v1/ai/predictive/asset-101/explain")
    assert response.status_code == 200
    assert response.json()["data"]["asset_id"] == "asset-101"


def test_graphrag_query_pure_relay(monkeypatch):
    async def fake_call_ai(path, *, payload=None, method="POST"):
        assert path == "/api/v1/graphrag/query"
        assert method == "POST"
        return {"answer": "42", "sources": []}

    monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)
    response = client.post("/api/v1/ai/graphrag/query", json={"query": "why?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "42", "sources": []}


def test_chat_pure_relay(monkeypatch):
    async def fake_call_ai(path, *, payload=None, method="POST"):
        assert path == "/api/v1/chat"
        return {"reply": "hello"}

    monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)
    response = client.post("/api/v1/ai/chat", json={"message": "hi"})
    assert response.status_code == 200
    assert response.json() == {"reply": "hello"}


def test_knowledge_search_pure_relay(monkeypatch):
    async def fake_call_ai(path, *, payload=None, method="GET"):
        assert path == "/api/v1/knowledge/search?q=bearing"
        return {"results": []}

    monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)
    response = client.get("/api/v1/ai/knowledge/search", params={"q": "bearing"})
    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_decision_recommendation_pure_relay(monkeypatch):
    async def fake_call_ai(path, *, payload=None, method="GET"):
        assert path == "/api/v1/decision/asset-101/recommendation"
        return {"recommendation": "replace bearing"}

    monkeypatch.setattr(ai_proxy, "call_ai", fake_call_ai)
    response = client.get("/api/v1/ai/decision/asset-101/recommendation")
    assert response.status_code == 200
    assert response.json() == {"recommendation": "replace bearing"}


async def test_call_ai_returns_ai_unavailable_envelope_on_dead_host(monkeypatch):
    """Part 4 Stage 1 checkpoint: a dead ai-platform host must not hang or 500."""
    monkeypatch.setattr(ai_client.settings, "AI_SERVICE_URL", "http://127.0.0.1:1")
    monkeypatch.setattr(ai_client.settings, "AI_SERVICE_TIMEOUT", 1)

    result = await ai_client.call_ai("/api/v1/predictive/infer", payload={}, method="POST")

    assert result == {
        "error": {
            "code": "AI_UNAVAILABLE",
            "message": "AI service is temporarily unavailable",
        }
    }


def test_predictive_infer_ai_unavailable_relayed_through_gateway(monkeypatch):
    """The gateway route itself must surface the AI_UNAVAILABLE envelope, not crash."""

    async def unavailable_call_ai(path, *, payload=None, method="POST"):
        return {"error": {"code": "AI_UNAVAILABLE", "message": "AI service is temporarily unavailable"}}

    monkeypatch.setattr(ai_proxy, "call_ai", unavailable_call_ai)

    response = client.post("/api/v1/ai/predictive/infer", json={"asset_id": "asset-101"})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
