"""
状态追踪器 - 追踪任务和系统状态
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(Enum):
    """会话状态枚举"""
    IDLE = "idle"
    ACTIVE = "active"
    RESTARTING = "restarting"
    ERROR = "error"


@dataclass
class TaskState:
    """任务状态"""
    task_file: str
    status: TaskStatus
    progress: float  # 0.0 - 1.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    last_updated: Optional[str] = None
    error_message: Optional[str] = None
    restart_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskState':
        """从字典创建"""
        data['status'] = TaskStatus(data['status'])
        return cls(**data)


@dataclass
class SessionState:
    """会话状态"""
    session_id: Optional[str]
    status: SessionStatus
    current_task: Optional[str]
    context_usage: float
    started_at: Optional[str]
    last_activity: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """从字典创建"""
        data['status'] = SessionStatus(data['status'])
        return cls(**data)


class StateTracker:
    """状态追踪器"""

    def __init__(self, state_file: str = "./state.json"):
        """
        初始化状态追踪器

        Args:
            state_file: 状态文件路径
        """
        self.state_file = Path(state_file)
        self.tasks: Dict[str, TaskState] = {}
        self.session: Optional[SessionState] = None

        # 加载已保存的状态
        self._load_state()

    def _load_state(self):
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 加载任务状态
                if 'tasks' in data:
                    self.tasks = {
                        task_file: TaskState.from_dict(task_data)
                        for task_file, task_data in data['tasks'].items()
                    }

                # 加载会话状态
                if 'session' in data and data['session']:
                    self.session = SessionState.from_dict(data['session'])

            except Exception as e:
                print(f"⚠️  加载状态失败: {e}")

    def _save_state(self):
        """保存状态"""
        try:
            data = {
                'tasks': {
                    task_file: task_state.to_dict()
                    for task_file, task_state in self.tasks.items()
                },
                'session': self.session.to_dict() if self.session else None,
                'last_saved': datetime.now().isoformat()
            }

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️  保存状态失败: {e}")

    def update_task_status(
        self,
        task_file: str,
        status: TaskStatus,
        progress: float = 0.0,
        error_message: Optional[str] = None
    ):
        """
        更新任务状态

        Args:
            task_file: 任务文件路径
            status: 任务状态
            progress: 进度
            error_message: 错误消息
        """
        now = datetime.now().isoformat()

        if task_file in self.tasks:
            task_state = self.tasks[task_file]
            task_state.status = status
            task_state.progress = progress
            task_state.last_updated = now

            if error_message:
                task_state.error_message = error_message

            if status == TaskStatus.IN_PROGRESS and not task_state.started_at:
                task_state.started_at = now

            if status == TaskStatus.COMPLETED:
                task_state.completed_at = now

        else:
            # 创建新任务状态
            self.tasks[task_file] = TaskState(
                task_file=task_file,
                status=status,
                progress=progress,
                started_at=now if status == TaskStatus.IN_PROGRESS else None,
                completed_at=now if status == TaskStatus.COMPLETED else None,
                last_updated=now,
                error_message=error_message
            )

        self._save_state()

    def update_session_status(
        self,
        session_id: Optional[str],
        status: SessionStatus,
        current_task: Optional[str] = None,
        context_usage: float = 0.0
    ):
        """
        更新会话状态

        Args:
            session_id: 会话ID
            status: 会话状态
            current_task: 当前任务
            context_usage: 上下文使用率
        """
        now = datetime.now().isoformat()

        if self.session:
            self.session.session_id = session_id
            self.session.status = status
            self.session.current_task = current_task
            self.session.context_usage = context_usage
            self.session.last_activity = now
        else:
            self.session = SessionState(
                session_id=session_id,
                status=status,
                current_task=current_task,
                context_usage=context_usage,
                started_at=now,
                last_activity=now
            )

        self._save_state()

    def increment_restart_count(self, task_file: str):
        """增加重启计数"""
        if task_file in self.tasks:
            self.tasks[task_file].restart_count += 1
            self._save_state()

    def get_task_state(self, task_file: str) -> Optional[TaskState]:
        """获取任务状态"""
        return self.tasks.get(task_file)

    def get_session_state(self) -> Optional[SessionState]:
        """获取会话状态"""
        return self.session

    def get_all_tasks(self) -> Dict[str, TaskState]:
        """获取所有任务状态"""
        return self.tasks

    def get_pending_tasks(self) -> List[str]:
        """获取待处理任务列表"""
        return [
            task_file
            for task_file, task_state in self.tasks.items()
            if task_state.status == TaskStatus.PENDING
        ]

    def get_in_progress_tasks(self) -> List[str]:
        """获取进行中任务列表"""
        return [
            task_file
            for task_file, task_state in self.tasks.items()
            if task_state.status == TaskStatus.IN_PROGRESS
        ]

    def clear_completed_tasks(self):
        """清理已完成任务"""
        self.tasks = {
            task_file: task_state
            for task_file, task_state in self.tasks.items()
            if task_state.status != TaskStatus.COMPLETED
        }
        self._save_state()

    def export_report(self) -> Dict[str, Any]:
        """
        导出报告

        Returns:
            包含所有状态信息的报告
        """
        return {
            'tasks': {
                task_file: task_state.to_dict()
                for task_file, task_state in self.tasks.items()
            },
            'session': self.session.to_dict() if self.session else None,
            'statistics': {
                'total_tasks': len(self.tasks),
                'pending': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                'in_progress': len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
                'completed': len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                'failed': len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            },
            'generated_at': datetime.now().isoformat()
        }
