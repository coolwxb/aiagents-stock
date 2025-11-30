"""
FastAPI应用入口
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.response import success_response
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="AI股票分析系统API",
    version="1.0.0",
    description="基于FastAPI的AI股票分析系统后端API",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一HTTP异常响应结构"""
    detail = exc.detail
    if isinstance(detail, dict) and {"code", "msg", "data"} <= set(detail.keys()):
        content = detail
    else:
        content = {
            "code": exc.status_code,
            "msg": detail if isinstance(detail, str) else str(detail),
            "data": None,
        }
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一请求参数校验错误"""
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "msg": "请求参数校验失败",
            "data": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """统一兜底异常"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": "服务器内部错误",
            "data": str(exc),
        },
    )


@app.get("/")
async def root():
    """根路径"""
    return success_response(
        {
            "message": "AI股票分析系统API",
            "version": "1.0.0",
            "docs": "/api/docs",
        }
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return success_response({"status": "healthy"}, msg="healthy")

