"""Fast, dependency-aware Phase 3 smoke check used by CI and operators."""
from fastapi.testclient import TestClient
from app.main import create_app

app = create_app()
client = TestClient(app, raise_server_exceptions=False)
for path in ("/api/v1/health/live", "/health"):
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code, response.text)
print("Phase 3 smoke checks passed")
