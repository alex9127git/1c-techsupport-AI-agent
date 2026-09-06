import pytest


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/api/kb", None),
        ("POST", "/api/kb", {"title": "Док", "content": "Текст", "tags": ["1c"]}),
        ("GET", "/api/kb/1", None),
        ("PUT", "/api/kb/1", {"title": "Док", "content": "Текст", "tags": []}),
        ("DELETE", "/api/kb/1", None),
        ("GET", "/api/dashboard", None),
        ("GET", "/api/settings", None),
        ("GET", "/api/escalations", None),
        ("GET", "/api/logs", None),
        ("GET", "/api/integrations", None),
        ("POST", "/api/integrations/bitrix/webhook", {"webhook_url": "http://x", "chat_id": "1"}),
        ("POST", "/api/integrations/redmine/webhook", {"url": "http://x", "api_key": "k", "project_id": "p"}),
    ],
)
def test_endpoints_return_contract(client, method, path, body):
    resp = client.open(path, method=method, json=body)
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["ok"] is True
    assert "data" in payload


def test_chat_endpoint(client):
    resp = client.post("/api/chat", json={"message": "как обновить 1С?"})
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["ok"] is True
    data = payload["data"]
    assert "answer" in data and "status" in data


def test_chat_image_endpoint(client):
    resp = client.post("/api/chat/image", data={"message": "что на скрине?"})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
