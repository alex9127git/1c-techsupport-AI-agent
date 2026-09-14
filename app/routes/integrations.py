from flask import jsonify, request
from flask.blueprints import Blueprint

from app.schemas.common import ok
from app.schemas.integrations import BitrixConnectIn, RedmineConnectIn
from app.routes import get_container

bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")


@bp.get("")
def list_integrations():
    result = get_container().integrations_service().list_channels()
    return jsonify(ok(result.model_dump()))


@bp.post("/bitrix/webhook")
def bitrix_webhook():
    body = BitrixConnectIn.model_validate(request.get_json(silent=True))
    result = get_container().integrations_service().connect_bitrix(body)
    return jsonify(ok(result.model_dump()))


@bp.post("/redmine/webhook")
def redmine_webhook():
    body = RedmineConnectIn.model_validate(request.get_json(silent=True))
    result = get_container().integrations_service().connect_redmine(body)
    return jsonify(ok(result.model_dump()))


@bp.post("/bitrix/receive")
def bitrix_receive():
    """Приём события от Bitrix24 (ONIMBOTV2MESSAGEADD и др.)."""
    payload = _load_payload()
    service = get_container().integrations_service()
    result = service.process_bitrix(payload)
    return jsonify(ok(result))


@bp.post("/redmine/receive")
def redmine_receive():
    """Приём вебхука от Redmine (плагин redmine_webhook)."""
    payload = _load_payload()
    service = get_container().integrations_service()
    result = service.process_redmine(payload)
    return jsonify(ok(result))


def _load_payload() -> dict:
    """Читает тело запроса: JSON или form-urlencoded (формат Bitrix24).

    Bitrix24 шлёт вебхуки как application/x-www-form-urlencoded с ключами
    вида data[bot][id]; Flask кладёт их в request.form.
    """
    json_body = request.get_json(silent=True)
    if isinstance(json_body, dict) and json_body:
        return json_body
    form = request.form.to_dict()
    if form:
        return form
    return {}