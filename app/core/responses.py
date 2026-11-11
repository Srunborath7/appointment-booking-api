from typing import Any, Dict, List, Optional

from .enum import StatusCode
from .lib.translate import get_translation


def app_success(
    msg: Optional[str] = None,
    code: int = StatusCode.OK,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    return {"code": code, "msg": msg or get_translation("success"), "data": data}


def app_success_paginated(
    data: Optional[Any] = None,
    msg: Optional[str] = None,
    code: int = StatusCode.OK,
    total_records: Optional[int] = None,
    total_pages: Optional[int] = None,
    current_page: Optional[int] = None,
    page_size: Optional[int] = None,
    lists: Optional[List[Dict]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    response: Dict[str, Any] = {
        "code": code,
        "msg": msg or get_translation("success"),
    }
    if all(v is not None for v in [total_records, total_pages, current_page, page_size, lists]):
        base_data: Dict[str, Any] = {
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
        }
        if extra:
            base_data.update(extra)
        base_data["lists"] = lists
        response["data"] = base_data
    else:
        response["data"] = data
    return response
