"""
配置管理API
"""
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_database
from app.services.config_service import ConfigService

router = APIRouter()


@router.get("")
async def get_config(db: Session = Depends(get_database)):
    """获取配置"""
    service = ConfigService(db)
    try:
        result = await service.get_config()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("")
async def update_config(
    config_data: dict,
    db: Session = Depends(get_database)
):
    """更新配置"""
    service = ConfigService(db)
    try:
        result = await service.update_config(config_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/validate")
async def validate_config(
    config_data: dict,
    db: Session = Depends(get_database)
):
    """验证配置"""
    service = ConfigService(db)
    try:
        result = await service.validate_config(config_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/test")
async def test_config_get(
    config_type: str,
    db: Session = Depends(get_database)
):
    """测试配置（兼容GET调用）"""
    service = ConfigService(db)
    try:
        result = await service.test_config(config_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/test")
async def test_config_post(
    payload: dict = Body(...),
    db: Session = Depends(get_database)
):
    """测试配置（推荐POST）"""
    service = ConfigService(db)
    try:
        config_type = payload.get("config_type")
        result = await service.test_config(config_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

