from llm_gateway.policy.auth import mask_api_key


def test_models_rejects_missing_authorization(client):
    response = client.get("/v1/models")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "message": "Invalid or missing API key.",
            "type": "authentication_error",
            "code": "invalid_api_key",
        }
    }


def test_mask_api_key_uses_gateway_prefix_and_suffix():
    assert mask_api_key("sk-gw-1234567890abcd") == "sk-gw-****abcd"
