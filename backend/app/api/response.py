"""
API 响应辅助工具
"""
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(data: Any = None, msg: str = "success", code: int = 200) -> dict:
    """统一成功返回结构"""
    return {
        "code": code,
        "message": msg,
        "data": jsonable_encoder(data),
    }


def error_response(
    msg: str = "error",
    code: int = 500,
    data: Any = None
) -> dict:
    """统一错误返回结构"""
    return {
        "code": code,
        "message": msg,
        "data": jsonable_encoder(data),
    }

