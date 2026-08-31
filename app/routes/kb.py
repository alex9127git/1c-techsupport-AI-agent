from flask import jsonify, request
from flask.blueprints import Blueprint

from app.schemas.common import ok
from app.routes import get_container

bp = Blueprint("kb", __name__, url_prefix="/api/kb")


@bp.get("")
def list_documents():
    result = get_container().knowledge_service().list_documents()
    return jsonify(ok(result.model_dump()))


@bp.post("")
def create_document():
    from app.schemas.kb import KbDocumentIn

    body = KbDocumentIn.model_validate(request.get_json(silent=True))
    result = get_container().knowledge_service().create_document(body)
    return jsonify(ok(result.model_dump()))


@bp.get("/<int:doc_id>")
def get_document(doc_id: int):
    result = get_container().knowledge_service().get_document(doc_id)
    return jsonify(ok(result.model_dump()))


@bp.put("/<int:doc_id>")
def update_document(doc_id: int):
    from app.schemas.kb import KbDocumentIn

    body = KbDocumentIn.model_validate(request.get_json(silent=True))
    result = get_container().knowledge_service().update_document(doc_id, body)
    return jsonify(ok(result.model_dump()))


@bp.delete("/<int:doc_id>")
def delete_document(doc_id: int):
    result = get_container().knowledge_service().delete_document(doc_id)
    return jsonify(ok(result.model_dump()))
