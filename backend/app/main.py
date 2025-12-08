"""
FastAPI应用入口
"""
import os
import sys

# 在导入其他模块之前，先添加 xtquant 路径
def _init_xtquant_path():
    """初始化 xtquant 模块路径"""
    try:
        # 计算项目根目录路径
        # 从 backend/app/main.py 向上3级到项目根目录
        current_file = os.path.abspath(__file__)
        backend_dir = os.path.dirname(os.path.dirname(current_file))
        project_root = os.path.dirname(backend_dir)
        
        # xtquant 需要项目根目录在 sys.path 中才能正确导入
        # 将项目根目录添加到 sys.path（如果还没有添加）
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            print(f"✅ 已添加项目根目录到路径: {project_root}")
        
        # 验证 xtquant 目录是否存在
        xtquant_path = os.path.join(project_root, 'xtquant')
        if os.path.exists(xtquant_path):
            print(f"✅ xtquant 目录存在: {xtquant_path}")
            return True
        else:
            print(f"⚠️ xtquant 目录不存在: {xtquant_path}")
            return False
    except Exception as e:
        print(f"⚠️ 初始化 xtquant 路径失败: {e}")
        return False

# 启动时初始化路径
_init_xtquant_path()

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.response import success_response
from app.api.v1.router import api_router
from app.core.config import settings
from app.database import SessionLocal
from app.models.config import AppConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：从数据库加载配置并初始化服务
    print("\n" + "="*60)
    print("正在从数据库加载配置...")
    print("="*60)
    
    db = SessionLocal()
    try:
        # 从数据库加载配置
        configs = db.query(AppConfig).all()
        config_dict = {cfg.key: cfg.value for cfg in configs}
        
        # 初始化数据源管理器
        from app.data.data_source import data_source_manager
        data_source_manager.load_config(config_dict)
        print("✅ 数据源管理器初始化完成")
        
        # 初始化QMT服务
        from app.services.qmt_service import qmt_service
        qmt_service.load_config(db)
        print("✅ QMT服务配置加载完成")
        
    except Exception as e:
        print(f"⚠️ 配置加载失败: {e}")
        print("将使用默认配置")
    finally:
        db.close()
    
    print("="*60)
    print("服务启动完成")
    print("="*60 + "\n")
    
    yield
    
    # 关闭时清理
    print("\n服务正在关闭...")


app = FastAPI(
    title="AI股票分析系统API",
    version="1.0.0",
    description="基于FastAPI的AI股票分析系统后端API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
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

