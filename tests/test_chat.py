def test_chat_completions_success_with_valid_key(client, auth_headers):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={
            "model": "chat-fast",
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.2,
            "max_tokens": 32,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == response.headers["x-request-id"]
    assert body["object"] == "chat.completion"
    assert body["model"] == "chat-fast"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"] == "Mock response from mock/mock-chat: hello"
    assert body["usage"]["prompt_tokens"] > 0
    assert body["usage"]["completion_tokens"] > 0
    assert body["usage"]["total_tokens"] > 0


def test_unknown_model_alias_returns_model_not_found(client, auth_headers):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={"model": "missing-model", "messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "model_not_found"

