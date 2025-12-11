"""
配置管理模块
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


def _get_default_database_url() -> str:
    """获取默认数据库URL，使用统一的sqlite_db目录"""
    # 从config.py向上找到项目根目录
    # backend/app/config.py -> backend/app -> backend -> 项目根目录
    current_dir = Path(__file__).resolve().parent  # backend/app
    project_root = current_dir.parent.parent  # backend -> 项目根目录
    sqlite_db_dir = project_root / "sqlite_db"
    sqlite_db_dir.mkdir(parents=True, exist_ok=True)
    db_path = sqlite_db_dir / "stock_analysis.db"
    return f"sqlite:///{db_path}"


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "AI股票分析系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://localhost:9528",  # Vue 前端开发服务器
        "http://127.0.0.1:8000",
        "http://127.0.0.1:9528",
        "http://localhost:3000"
    ]
    
    # 数据库配置
    DATABASE_URL: str = _get_default_database_url()
    
    # JWT配置
    SECRET_KEY: str = "ai-agent-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = "sk-867410930e1e428d881e1ddf5ec056eb"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    
    # 数据源配置
    TUSHARE_TOKEN: str = ""
    TDX_ENABLED: bool = False
    TDX_BASE_URL: str = "http://localhost:8080"
    
    # MySQL行情数据库配置
    MYSQL_ENABLED: bool = True
    MYSQL_HOST: str = "82.156.239.131"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "1q2w#E$R"
    MYSQL_DATABASE: str = "choose_stock"
    MYSQL_STOCK_TABLE: str = "stock_history"
    
    # 邮件配置
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: str = "smtp.qq.com"
    SMTP_PORT: int = 587
    EMAIL_FROM: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_TO: str = ""
    
    # Webhook配置
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_TYPE: str = "dingtalk"  # dingtalk or feishu
    WEBHOOK_URL: str = ""
    WEBHOOK_KEYWORD: str = "股票"
    
    # MiniQMT配置
    MINIQMT_ENABLED: bool = False
    MINIQMT_ACCOUNT_ID: str = ""
    MINIQMT_ACCOUNT_TYPE: str = "STOCK"
    MINIQMT_USERDATA_PATH: str = "E:\\zhongjin_qmt\\userdata_mini"
    
    # Redis配置（可选）
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例）"""
    return Settings()


settings = get_settings()

