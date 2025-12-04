"""
数据管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.response import success_response
from app.dependencies import get_database
from app.services.data_management_service import DataManagementService

router = APIRouter()


@router.post("/sectors/update")
async def update_sectors(db: Session = Depends(get_database)):
    """更新板块数据"""
    service = DataManagementService(db)
    try:
        result = await service.update_sectors()
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return success_response(result, msg="板块数据更新成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sectors/stocks/update")
async def update_sector_stocks(
    sector_code: Optional[str] = Query(None, description="板块代码,不传则更新所有板块"),
    db: Session = Depends(get_database)
):
    """更新板块成分股"""
    service = DataManagementService(db)
    try:
        result = await service.update_sector_stocks(sector_code)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return success_response(result, msg="板块成分股更新成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stocks/update")
async def update_stock_info(
    stock_code: Optional[str] = Query(None, description="股票代码,不传则更新所有板块成分股"),
    db: Session = Depends(get_database)
):
    """更新股票基本信息"""
    service = DataManagementService(db)
    try:
        result = await service.update_stock_info(stock_code)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return success_response(result, msg="股票信息更新成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors")
async def get_sectors(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="板块类别筛选"),
    db: Session = Depends(get_database)
):
    """获取板块列表"""
    service = DataManagementService(db)
    try:
        result = await service.get_sectors(page, page_size, category)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks")
async def get_stocks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sector_code: Optional[str] = Query(None, description="板块代码筛选"),
    db: Session = Depends(get_database)
):
    """获取股票列表"""
    service = DataManagementService(db)
    try:
        result = await service.get_stocks(page, page_size, sector_code)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
