from flask import jsonify, request
from flask.blueprints import Blueprint

from app.schemas.common import ok
from app.schemas.integrations import BitrixConnectIn, RedmineConnectIn
from app.routes import get_container

bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")


@bp.get("")
def list_integrations():
    return jsonify(ok({"channels": [{"channel": "bitrix", "enabled": False}, {"channel": "redmine", "enabled": False}]}))


@bp.post("/bitrix/webhook")
def bitrix_webhook():
    _ = BitrixConnectIn.model_validate(request.get_json(silent=True))
    return jsonify(ok({"status": "not_implemented"}))


@bp.post("/redmine/webhook")
def redmine_webhook():
    _ = RedmineConnectIn.model_validate(request.get_json(silent=True))
    return jsonify(ok({"status": "not_implemented"}))
