from typing import TypedDict, List, Dict, Any
from typing_extensions import NotRequired

class ErrorType(TypedDict):
    status: int
    error: str
    message: str

class PaginationPayload(TypedDict):
    cursor: NotRequired[str]

class BasePayload(TypedDict):
    data: List[Dict[str, Any]]
    pagination: NotRequired[PaginationPayload]
