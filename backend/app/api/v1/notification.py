"""
通知服务API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_database
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/email")
async def send_email(
    email_data: dict,
    db: Session = Depends(get_database)
):
    """发送邮件"""
    service = NotificationService(db)
    try:
        result = await service.send_email(email_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def send_webhook(
    webhook_data: dict,
    db: Session = Depends(get_database)
):
    """发送Webhook"""
    service = NotificationService(db)
    try:
        result = await service.send_webhook(webhook_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """通知历史"""
    service = NotificationService(db)
    try:
        result = await service.get_history(page, page_size)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_notification(
    notification_type: str,
    db: Session = Depends(get_database)
):
    """测试通知"""
    service = NotificationService(db)
    try:
        result = await service.test_notification(notification_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

