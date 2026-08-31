from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ResultStatus(StrEnum):
    OK = "ok"
    NOT_IMPLEMENTED = "not_implemented"
    ERROR = "error"


class ApiData(BaseModel):
    """Обёртка успешного ответа: {"ok": true, "data": {...}}."""

    ok: bool = True
    data: dict[str, Any]


class ApiError(BaseModel):
    """Обёртка ошибки: {"ok": false, "error": {"code", "message"}}."""

    ok: bool = False
    error: dict[str, str]


def ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": data}


def fail(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


class ApiException(Exception):
    """Исключение с HTTP-статусом для централизованной обработки ошибок."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
