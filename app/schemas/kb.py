from pydantic import BaseModel, Field

from app.schemas.common import ResultStatus


class KbDocumentIn(BaseModel):
    title: str = Field(min_length=1)
    content: str = ""
    tags: list[str] = []


class KbDocumentOut(BaseModel):
    id: int | None = None
    title: str = ""
    content: str = ""
    tags: list[str] = []
    status: ResultStatus = ResultStatus.NOT_IMPLEMENTED
    source_file: str | None = None
    indexed: bool = False


class KbListOut(BaseModel):
    items: list[dict] = []
    total: int = 0


class KbCreateOut(BaseModel):
    id: int | None = None
    accepted: bool = True
    status: ResultStatus = ResultStatus.NOT_IMPLEMENTED
    indexed: bool = False


class KbMutateOut(BaseModel):
    ok: bool = True
    status: ResultStatus = ResultStatus.NOT_IMPLEMENTED
