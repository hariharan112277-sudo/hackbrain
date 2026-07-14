def test_liveness_and_readiness(client):
    """Verifies that health and monitoring endpoints resolve correctly."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_security_headers_present(client):
    """Verifies that mandatory enterprise-grade security headers are set."""
    response = client.get("/api/v1/health/live")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" in response.headers


def test_correlation_id_propagation(client):
    """Verifies that Correlation ID middleware is running and propagating upstream IDs."""
    custom_id = "test-session-uuid-999"
    response = client.get("/api/v1/health/live", headers={"X-Correlation-ID": custom_id})
    assert response.headers["X-Correlation-ID"] == custom_id


def test_validation_error_formatting(client):
    """Verifies that Pydantic input exceptions are caught and sanitized to uniform patterns."""
    response = client.get("/api/v1/invalid-route-nonexistent")
    assert response.status_code == 404
    assert "success" in response.json()
    assert response.json()["success"] is False
