def test_app_creates(app):
    assert app is not None
    assert app.testing


def test_health(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200


def test_root_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "1C Techsupport AI Agent" in resp.get_data(as_text=True)
