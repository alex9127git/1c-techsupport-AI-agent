from flask import jsonify, request
from flask.blueprints import Blueprint

from app.schemas.chat import ChatRequest, ChatResponse, ImageResponse
from app.schemas.common import ok
from app.routes import get_container

bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@bp.post("")
def chat():
    body = ChatRequest.model_validate(request.get_json(silent=True))
    result = get_container().agent_service().answer_question(body)
    return jsonify(ok(result.model_dump()))


@bp.post("/image")
def chat_image():
    file = request.files.get("file")
    if file is None or not file.filename:
        from app.schemas.common import ApiException

        raise ApiException(400, "file_required", "Изображение не передано (поле 'file')")
    message = request.form.get("message")
    result = get_container().agent_service().analyze_image(file, message)
    return jsonify(ok(result.model_dump()))
