from flask import jsonify, request
from flask.blueprints import Blueprint

from app.schemas.admin import SettingsIn
from app.schemas.common import ok
from app.routes import get_container

bp = Blueprint("admin", __name__, url_prefix="/api")


@bp.get("/dashboard")
def dashboard():
    result = get_container().metrics_service().dashboard()
    return jsonify(ok(result.model_dump()))


@bp.get("/settings")
def get_settings():
    result = get_container().settings_service().as_dict()
    return jsonify(ok(result))


@bp.put("/settings")
def update_settings():
    body = SettingsIn.model_validate(request.get_json(silent=True))
    result = get_container().settings_service().update(body.confidence_threshold, body.escalation_strategy)
    return jsonify(ok(result))


@bp.get("/escalations")
def escalations():
    result = get_container().metrics_service().escalations()
    return jsonify(ok(result.model_dump()))


@bp.get("/logs")
def logs():
    result = get_container().metrics_service().logs()
    return jsonify(ok(result.model_dump()))
