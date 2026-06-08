def test_models_success_with_valid_key(client, auth_headers):
    response = client.get("/v1/models", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    model_ids = [item["id"] for item in body["data"]]
    assert body["object"] == "list"
    assert model_ids == ["chat-fast", "chat-smart"]

