"""
API依赖项（认证等）
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.data.data_source import get_data_source_manager, DataSourceManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    获取当前用户（JWT认证）
    注意：当前版本为简化实现，实际使用时需要完善用户认证逻辑
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # TODO: 从payload中获取用户信息
        return payload
    except JWTError:
        raise credentials_exception


def get_data_source(db: Session = Depends(get_db)) -> DataSourceManager:
    """
    获取数据源管理器实例（从数据库配置初始化）
    
    Args:
        db: 数据库会话
    
    Returns:
        DataSourceManager: 已配置的数据源管理器实例
    """
    from app.services.config_service import ConfigService
    
    try:
        # 从数据库加载配置
        config_service = ConfigService(db)
        config = config_service._load_config()
        
        # 使用配置初始化数据源管理器
        return get_data_source_manager(config)
    except Exception as e:
        # 如果加载配置失败，返回默认实例（仅使用 Akshare）
        print(f"⚠️ 从数据库加载配置失败，使用默认数据源: {e}")
        return get_data_source_manager()

