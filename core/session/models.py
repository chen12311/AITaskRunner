"""
会话数据模型 - 定义会话状态和管理会话的数据结构
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from core.cli_monitor import CLIMonitor
    from core.terminal_adapters.base import TerminalAdapter
    from core.cli_adapters.base import CLIAdapter


class SessionStatus(Enum):
    """会话状态枚举"""
    IDLE = "idle"           # 空闲，尚未启动
    STARTING = "starting"   # 正在启动
    RUNNING = "running"     # 运行中
    STOPPING = "stopping"   # 正在停止
    STOPPED = "stopped"     # 已停止
    ERROR = "error"         # 错误状态


@dataclass
class ManagedSession:
    """
    管理会话 - 代表一个独立的 CLI 会话实例

    每个任务拥有独立的会话，包含独立的 CLIMonitor、TerminalAdapter 和 CLIAdapter 实例。
    """
    task_id: str                                    # 任务ID，唯一标识
    monitor: "CLIMonitor"                           # CLI 监控器实例
    terminal: "TerminalAdapter"                     # 终端适配器实例
    cli_adapter: "CLIAdapter"                       # CLI 适配器实例
    status: SessionStatus = SessionStatus.IDLE     # 当前状态
    project_dir: str = ""                           # 项目目录
    doc_path: str = ""                              # 任务文档路径
    cli_type: str = "claude_code"                   # CLI 类型
    api_base_url: str = "http://127.0.0.1:8086"     # API 基础 URL
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    started_at: Optional[datetime] = None           # 启动时间
    stopped_at: Optional[datetime] = None           # 停止时间
    monitor_task: Optional[asyncio.Task] = None     # 监控任务
    error_message: Optional[str] = None             # 错误信息
    semaphore_acquired: bool = False                # 是否已占用 semaphore 槽位

    def to_dict(self) -> dict:
        """转换为字典，用于 API 响应"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "project_dir": self.project_dir,
            "doc_path": self.doc_path,
            "cli_type": self.cli_type,
            "api_base_url": self.api_base_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "error_message": self.error_message,
            "terminal_name": self.terminal.name if self.terminal else None,
            "cli_name": self.cli_adapter.name if self.cli_adapter else None,
        }

    def is_active(self) -> bool:
        """是否处于活跃状态（启动中或运行中）"""
        return self.status in (SessionStatus.STARTING, SessionStatus.RUNNING)

    def verify_alive(self) -> bool:
        """
        验证会话是否真的存活（检查终端窗口是否存在）

        如果状态为活跃但窗口已死，自动标记为停止
        返回 True 表示会话真的活跃，False 表示已死或已清理
        """
        if not self.is_active():
            return False

        # 检查终端窗口是否真的存在
        if self.terminal and not self.terminal.is_window_alive():
            print(f"🔄 检测到幽灵会话 {self.task_id}，自动清理")
            self.mark_stopped()
            self.terminal.clear_session()
            return False

        return True

    def is_terminal(self) -> bool:
        """是否处于终止状态（已停止或错误）"""
        return self.status in (SessionStatus.STOPPED, SessionStatus.ERROR)

    def mark_starting(self):
        """标记为启动中"""
        self.status = SessionStatus.STARTING
        self.started_at = datetime.now()

    def mark_running(self):
        """标记为运行中"""
        self.status = SessionStatus.RUNNING

    def mark_stopping(self):
        """标记为停止中"""
        self.status = SessionStatus.STOPPING

    def mark_stopped(self):
        """标记为已停止"""
        self.status = SessionStatus.STOPPED
        self.stopped_at = datetime.now()

    def mark_error(self, message: str):
        """标记为错误状态"""
        self.status = SessionStatus.ERROR
        self.error_message = message
        self.stopped_at = datetime.now()
