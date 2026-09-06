def test_chat_requires_message(client):
    resp = client.post("/api/chat", json={})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_chat_rejects_empty_message(client):
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_kb_create_requires_title(client):
    resp = client.post("/api/kb", json={"content": "no title"})
    assert resp.status_code == 400
