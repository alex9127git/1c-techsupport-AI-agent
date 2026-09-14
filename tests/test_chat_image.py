from pathlib import Path

import pytest


def _png_bytes():
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_chat_image_requires_file(client):
    resp = client.post("/api/chat/image", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_chat_image_unsupported_extension(app, client):
    # Валидного AUTH_KEY нет — но проверка расширения выполняется раньше,
    # поэтому вернётся ERROR, а не not_configured.
    resp = client.post(
        "/api/chat/image",
        data={"file": (__import__("io").BytesIO(b"x"), "scr.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["accepted"] is False
    assert data["status"] == "error"
    assert "не поддерживается" in (data["error"] or "")


def test_chat_image_not_configured(app, client):
    resp = client.post(
        "/api/chat/image",
        data={"file": (__import__("io").BytesIO(_png_bytes()), "scr.png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["accepted"] is False
    assert data["status"] == "not_configured"


class FakeImageProvider:
    configured = True

    def analyze_image(self, prompt: str, image_path: str) -> str:
        assert Path(image_path).exists()
        return f"Анализ: {prompt}"


def test_chat_image_success(app, client):
    from app.routes import get_container

    with app.app_context():
        get_container().gigachat_provider = lambda: FakeImageProvider()

        resp = client.post(
            "/api/chat/image",
            data={"file": (__import__("io").BytesIO(_png_bytes()), "scr.png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["accepted"] is True
        assert data["status"] == "ok"
        assert "Анализ" in (data["analysis"] or "")


def test_chat_image_with_message(app, client):
    from app.routes import get_container

    with app.app_context():
        get_container().gigachat_provider = lambda: FakeImageProvider()

        resp = client.post(
            "/api/chat/image",
            data={
                "file": (__import__("io").BytesIO(_png_bytes()), "scr.png"),
                "message": "Что за ошибка?",
            },
            content_type="multipart/form-data",
        )
        data = resp.get_json()["data"]
        assert data["status"] == "ok"
        assert "Что за ошибка?" in data["analysis"]


class FailingImageProvider:
    configured = True

    def analyze_image(self, prompt: str, image_path: str) -> str:
        raise RuntimeError("сеть недоступна")


def test_chat_image_provider_error(app, client):
    from app.routes import get_container

    with app.app_context():
        get_container().gigachat_provider = lambda: FailingImageProvider()

        resp = client.post(
            "/api/chat/image",
            data={"file": (__import__("io").BytesIO(_png_bytes()), "scr.png")},
            content_type="multipart/form-data",
        )
        data = resp.get_json()["data"]
        assert data["accepted"] is False
        assert data["status"] == "error"
        assert data["error"]