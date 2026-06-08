import pytest
from fastapi.testclient import TestClient

from llm_gateway.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GATEWAY_API_KEYS", "test-key")
    monkeypatch.setenv("GATEWAY_CONFIG_DIR", "config")
    return TestClient(create_app())


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-key"}

