"""
进度追踪器 - 用于跟踪长时间运行任务的进度
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressTracker:
    """进度追踪器 - 使用内存存储"""
    
    def __init__(self):
        # 使用内存存储任务进度
        # key: task_id, value: task_info
        self._tasks: Dict[str, Dict[str, Any]] = {}
    
    def create_task(self, task_type: str, params: Dict[str, Any] = None) -> str:
        """创建新任务，返回task_id"""
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "status": TaskStatus.PENDING,
            "progress": 0,
            "current_step": "初始化任务...",
            "steps": [],
            "params": params or {},
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        return task_id
    
    def update_progress(
        self,
        task_id: str,
        progress: int,
        current_step: str,
        status: TaskStatus = TaskStatus.RUNNING
    ):
        """更新任务进度"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["progress"] = progress
        task["current_step"] = current_step
        task["status"] = status
        task["updated_at"] = datetime.now().isoformat()
        
        # 添加到步骤历史
        task["steps"].append({
            "step": current_step,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        })
        
        # 触发WebSocket推送
        self._notify_websocket(task_id)
    
    def add_step(self, task_id: str, step: str):
        """添加步骤记录"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["steps"].append({
            "step": step,
            "timestamp": datetime.now().isoformat()
        })
        task["updated_at"] = datetime.now().isoformat()
        self._notify_websocket(task_id)
    
    def complete_task(self, task_id: str, result: Any):
        """完成任务"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["status"] = TaskStatus.COMPLETED
        task["progress"] = 100
        task["current_step"] = "分析完成"
        task["result"] = result
        task["updated_at"] = datetime.now().isoformat()
        self._notify_websocket(task_id)
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["status"] = TaskStatus.FAILED
        task["current_step"] = "分析失败"
        task["error"] = error
        task["updated_at"] = datetime.now().isoformat()
        self._notify_websocket(task_id)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self._tasks.get(task_id)
    
    def _notify_websocket(self, task_id: str):
        """通知WebSocket客户端（异步）"""
        try:
            from app.core.websocket_manager import get_ws_manager
            ws_manager = get_ws_manager()
            task = self._tasks.get(task_id)
            if task:
                # 创建异步任务推送更新
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(ws_manager.send_progress(task_id, task))
                    else:
                        loop.run_until_complete(ws_manager.send_progress(task_id, task))
                except RuntimeError:
                    # 如果没有事件循环，创建一个新的
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(ws_manager.send_progress(task_id, task))
                    loop.close()
        except Exception as e:
            # 静默失败，不影响主流程
            import logging
            logging.debug(f"WebSocket通知失败: {e}")
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取所有进行中的任务"""
        active_tasks = []
        for task_id, task in self._tasks.items():
            if task["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                active_tasks.append(task)
        return active_tasks
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务（仅清理已完成或失败的任务）"""
        now = datetime.now()
        task_ids_to_remove = []
        
        for task_id, task in self._tasks.items():
            # 只清理已完成或失败的任务
            if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                created_at = datetime.fromisoformat(task["created_at"])
                age_hours = (now - created_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    task_ids_to_remove.append(task_id)
        
        for task_id in task_ids_to_remove:
            del self._tasks[task_id]


# 全局进度追踪器实例
_progress_tracker = ProgressTracker()


def get_progress_tracker() -> ProgressTracker:
    """获取全局进度追踪器实例"""
    return _progress_tracker
