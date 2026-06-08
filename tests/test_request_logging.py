import logging
from collections.abc import Iterator

import pytest

LOGGER_NAME = "llm_gateway.requests"


@pytest.fixture(autouse=True)
def capture_request_logs(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    yield


def _last_payload(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    records = [record for record in caplog.records if record.name == LOGGER_NAME]
    assert records
    payload = getattr(records[-1], "payload", None)
    assert isinstance(payload, dict)
    return payload


def test_models_success_writes_standard_request_log(client, auth_headers, caplog):
    response = client.get("/v1/models", headers=auth_headers)

    payload = _last_payload(caplog)
    assert response.status_code == 200
    assert payload["request_id"] == response.headers["x-request-id"]
    assert payload["method"] == "GET"
    assert payload["path"] == "/v1/models"
    assert payload["http_status"] == 200
    assert payload["status"] == "success"
    assert payload["api_key_prefix"] == "****-key"


def test_auth_failure_writes_request_log_with_request_id(client, caplog):
    response = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer sk-gw-1234567890abcd"},
    )

    payload = _last_payload(caplog)
    assert response.status_code == 401
    assert payload["request_id"] == response.headers["x-request-id"]
    assert payload["http_status"] == 401
    assert payload["status"] == "error"
    assert payload["error_code"] == "invalid_api_key"
    assert payload["api_key_prefix"] == "sk-gw-****abcd"


def test_validation_error_writes_request_log_with_request_id(client, auth_headers, caplog):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={"model": "chat-fast"},
    )

    payload = _last_payload(caplog)
    assert response.status_code == 422
    assert payload["request_id"] == response.headers["x-request-id"]
    assert payload["http_status"] == 422
    assert payload["status"] == "error"
    assert payload["error_code"] == "validation_error"


def test_stream_failure_writes_request_log_with_model_context(client, auth_headers, caplog):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={
            "model": "chat-fast",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
    )

    payload = _last_payload(caplog)
    assert response.status_code == 501
    assert payload["request_id"] == response.headers["x-request-id"]
    assert payload["http_status"] == 501
    assert payload["status"] == "error"
    assert payload["model_alias"] == "chat-fast"
    assert payload["error_code"] == "not_implemented"
