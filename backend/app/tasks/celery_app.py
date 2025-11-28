"""
Celery应用
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "stock_analysis",
    broker=settings.REDIS_URL if settings.REDIS_ENABLED else "redis://localhost:6379/0",
    backend=settings.REDIS_URL if settings.REDIS_ENABLED else "redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)

