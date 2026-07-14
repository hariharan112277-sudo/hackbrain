import pytest
from typing import Generator
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Initializes a clean, test-configured app instance."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
