from flask import Flask, jsonify, current_app, render_template
from flask.blueprints import Blueprint

from app.schemas.common import ApiException, fail
from app.services.container import ServiceContainer


def get_container() -> ServiceContainer:
    """Возвращает сервис-контейнер текущего приложения."""
    return current_app.extensions["container"]


def register_blueprints(app: Flask) -> None:
    container = ServiceContainer(app)
    app.extensions["container"] = container

    from pydantic import ValidationError

    from app.routes import admin, chat, integrations, kb

    for bp in (chat.bp, kb.bp, admin.bp, integrations.bp):
        app.register_blueprint(bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(ApiException)
    def handle_api_exception(exc: ApiException):
        response = jsonify(fail(exc.code, exc.message))
        response.status_code = exc.status_code
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        response = jsonify(fail("validation_error", "Invalid request body"))
        response.status_code = 400
        return response
