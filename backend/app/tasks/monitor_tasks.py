"""
监测任务
"""
from app.tasks.celery_app import celery_app


@celery_app.task
def monitor_stock_task(task_id: int):
    """监测股票任务"""
    # TODO: 实现监测任务逻辑
    pass

