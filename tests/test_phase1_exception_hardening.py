"""
Phase 1 — Critical Backend Bug Fixes & Stability Hardening
Validation Test Matrix (VAL-001 .. VAL-012)

Targeted regression suite that proves malformed / hostile payloads can NEVER
escalate a 4xx / DB error into a 500 Internal Server Error, and that the strict
JSON error contract is always returned.

Run (from repo root, with the project venv active):
    pytest tests/test_phase1_exception_hardening.py -v

The suite is self-contained: it imports the canonical handlers from
``app.core.exceptions`` and exercises them against a lightweight FastAPI app, so
it runs without a live database / Redis / MQTT broker.
"""
import asyncio
import json

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    create_error_response,
    request_validation_exception_handler,
    pydantic_validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
    sanitize_payload,
)


def _make_request(path: str = "/api/v1/assets") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [(b"content-type", b"application/json")],
        "query_string": b"",
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# Fixture: a minimal app wired exactly like app/main.py (handler set + the
# Phase 1 body-parse 400 -> 422 remap in the StarletteHTTPException handler).
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    class Echo(BaseModel):
        name: str
        value: float

    app = FastAPI()

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        if exc.status_code == 400 and isinstance(exc.detail, str) and "parsing the body" in exc.detail:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "VALIDATION_ERROR",
                    "message": "The request payload could not be parsed.",
                    "details": [exc.detail],
                },
            )
        if exc.status_code == 404:
            return JSONResponse(status_code=404, content={"success": False, "error": "NOT_FOUND", "message": str(exc.detail)})
        return JSONResponse(status_code=exc.status_code, content={"success": False, "error": "HTTP_ERROR", "message": str(exc.detail)})

    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    @app.post("/echo")
    def echo(m: Echo):
        return {"ok": True, "name": m.name}

    return TestClient(app)


# ---------------------------------------------------------------------------
# Handler-level unit tests
# ---------------------------------------------------------------------------
@pytest.mark.unit
async def test_request_validation_with_raw_bytes():
    """VAL-002/VAL-007 — bytes inside exc.errors() must not raise TypeError."""
    err = RequestValidationError(
        [
            {
                "type": "value_error",
                "loc": ("body", "name"),
                "msg": "value is not a valid string",
                "input": b"\x00\xFF\xAA garbage",
                "ctx": {"foo": b"\xDE\xAD\xBE\xEF"},
            }
        ]
    )
    resp = await request_validation_exception_handler(_make_request(), err)
    assert resp.status_code == 422
    body = json.loads(resp.body)
    assert body["success"] is False
    assert body["error"] == "VALIDATION_ERROR"
    assert isinstance(body["details"], list)


@pytest.mark.unit
async def test_pydantic_validation_error():
    perr = PydanticValidationError.from_exception_data(
        "Dummy", [{"type": "missing", "loc": ("x",), "msg": "Field required", "input": None}]
    )
    resp = await pydantic_validation_exception_handler(_make_request(), perr)
    assert resp.status_code == 422
    assert json.loads(resp.body)["error"] == "INTERNAL_VALIDATION_ERROR"


@pytest.mark.unit
async def test_sqlalchemy_integrity_conflict():
    ierr = IntegrityError("dup", None, Exception("duplicate key value"))
    resp = await sqlalchemy_exception_handler(_make_request(), ierr)
    assert resp.status_code == 409
    assert json.loads(resp.body)["error"] == "DATABASE_INTEGRITY_VIOLATION"


@pytest.mark.unit
async def test_sqlalchemy_generic_unavailable():
    derr = SQLAlchemyError("connection refused")
    resp = await sqlalchemy_exception_handler(_make_request(), derr)
    assert resp.status_code == 503
    assert json.loads(resp.body)["error"] == "DATABASE_UNAVAILABLE"


@pytest.mark.unit
async def test_global_exception_safe_schema():
    resp = await general_exception_handler(_make_request(), RuntimeError("boom"))
    assert resp.status_code == 500
    body = json.loads(resp.body)
    assert body["error"] == "INTERNAL_SERVER_ERROR"
    text = resp.body.decode()
    assert "Traceback" not in text  # raw traces must never leak
    assert "RuntimeError" not in text


@pytest.mark.unit
async def test_create_error_response_bytes_safe():
    resp = create_error_response(400, "TEST_CODE", "msg", details=[{"b": b"\x01\x02"}])
    assert resp.status_code == 400
    assert json.loads(resp.body)["error"] == "TEST_CODE"


@pytest.mark.unit
def test_sanitize_payload_handles_non_utf8_bytes():
    import datetime
    import decimal
    import enum
    import uuid

    class Color(enum.Enum):
        RED = "red"

    obj = {
        "raw": b"\xff\xfe binary",
        "uid": uuid.uuid4(),
        "when": datetime.datetime(2026, 1, 1),
        "amount": decimal.Decimal("1.5"),
        "color": Color.RED,
        "nest": [b"\x00", {"k": b"\xab"}],
    }
    out = sanitize_payload(obj)
    # Must be JSON serializable
    import json
    json.dumps(out)
    assert isinstance(out["raw"], str)
    assert out["color"] == "red"
    assert out["amount"] == 1.5


# ---------------------------------------------------------------------------
# End-to-end (TestClient) — the real 500 -> 422 hardening
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.security
def test_val001_malformed_json(client):
    r = client.post("/echo", content=b'{"name":', headers={"content-type": "application/json"})
    assert r.status_code == 422
    assert r.json()["error"] == "VALIDATION_ERROR"


@pytest.mark.unit
@pytest.mark.security
def test_val002_binary_injection(client):
    r = client.post("/echo", content=b"\x00\xFF\xAA", headers={"content-type": "application/json"})
    assert r.status_code == 422
    assert r.json()["error"] == "VALIDATION_ERROR"


@pytest.mark.unit
def test_val003_wrong_content_type(client):
    # application/json with invalid json still yields 422, not 500
    r = client.post("/echo", content=b"not-json", headers={"content-type": "application/json"})
    assert r.status_code in (400, 422)


@pytest.mark.unit
def test_val004_missing_fields(client):
    r = client.post("/echo", json={})
    assert r.status_code == 422


@pytest.mark.unit
def test_val005_wrong_type(client):
    r = client.post("/echo", json={"name": "x", "value": "not-a-float"})
    assert r.status_code == 422


@pytest.mark.unit
def test_val007_corrupted_multibyte(client):
    r = client.post("/echo", content="朱".encode("utf-8")[:-1], headers={"content-type": "application/json"})
    assert r.status_code in (400, 422)  # never 500


@pytest.mark.unit
def test_val008_null_on_strict(client):
    r = client.post("/echo", json={"name": None, "value": 1.0})
    assert r.status_code == 422


@pytest.mark.unit
def test_val009_empty_payload(client):
    r = client.post("/echo", content=b"", headers={"content-type": "application/json"})
    assert r.status_code == 422


@pytest.mark.unit
def test_val010_missing_body(client):
    r = client.post("/echo", headers={"content-type": "application/json"})
    assert r.status_code == 422


@pytest.mark.unit
async def test_val012_integrity_conflict_via_handler():
    # Directly exercise the SQLAlchemy 409 mapping through the handler pipeline.
    resp = await sqlalchemy_exception_handler(_make_request(), IntegrityError("dup", None, Exception("x")))
    assert resp.status_code == 409
    assert json.loads(resp.body)["error"] == "DATABASE_INTEGRITY_VIOLATION"
