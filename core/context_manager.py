"""
上下文管理器 - 管理Codex的上下文窗口
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ContextSnapshot:
    """上下文快照"""
    timestamp: datetime
    tokens_used: int
    max_tokens: int
    usage_percentage: float
    task_file: str
    task_progress: float


@dataclass
class ContextWindow:
    """上下文窗口信息"""
    current_tokens: int = 0
    max_tokens: int = 200000
    threshold: float = 0.8
    history: List[ContextSnapshot] = field(default_factory=list)

    @property
    def usage_percentage(self) -> float:
        """获取使用百分比"""
        if self.max_tokens == 0:
            return 0.0
        return self.current_tokens / self.max_tokens

    @property
    def should_restart(self) -> bool:
        """是否应该重启"""
        return self.usage_percentage >= self.threshold

    @property
    def available_tokens(self) -> int:
        """可用token数"""
        return self.max_tokens - self.current_tokens


class ContextManager:
    """上下文管理器"""

    def __init__(self, max_tokens: int = 200000, threshold: float = 0.8):
        """
        初始化上下文管理器

        Args:
            max_tokens: 最大token数
            threshold: 重启阈值（0-1之间）
        """
        self.context_window = ContextWindow(
            max_tokens=max_tokens,
            threshold=threshold
        )
        self.snapshots: List[ContextSnapshot] = []

    def update_context(self, current_tokens: int, task_file: str = "", task_progress: float = 0.0):
        """
        更新上下文信息

        Args:
            current_tokens: 当前使用的token数
            task_file: 任务文件路径
            task_progress: 任务进度（0-1）
        """
        self.context_window.current_tokens = current_tokens

        # 创建快照
        snapshot = ContextSnapshot(
            timestamp=datetime.now(),
            tokens_used=current_tokens,
            max_tokens=self.context_window.max_tokens,
            usage_percentage=self.context_window.usage_percentage,
            task_file=task_file,
            task_progress=task_progress
        )

        self.snapshots.append(snapshot)
        self.context_window.history.append(snapshot)

    def check_threshold(self) -> bool:
        """
        检查是否达到阈值

        Returns:
            是否需要重启会话
        """
        return self.context_window.should_restart

    def get_usage_stats(self) -> Dict[str, any]:
        """
        获取使用统计

        Returns:
            包含统计信息的字典
        """
        return {
            "current_tokens": self.context_window.current_tokens,
            "max_tokens": self.context_window.max_tokens,
            "usage_percentage": self.context_window.usage_percentage * 100,
            "available_tokens": self.context_window.available_tokens,
            "should_restart": self.context_window.should_restart,
            "total_snapshots": len(self.snapshots)
        }

    def reset_context(self):
        """重置上下文"""
        self.context_window.current_tokens = 0

    def get_recent_snapshots(self, count: int = 10) -> List[ContextSnapshot]:
        """
        获取最近的快照

        Args:
            count: 快照数量

        Returns:
            快照列表
        """
        return self.snapshots[-count:] if len(self.snapshots) >= count else self.snapshots

    def export_history(self) -> List[Dict]:
        """
        导出历史记录

        Returns:
            历史记录列表
        """
        return [
            {
                "timestamp": snapshot.timestamp.isoformat(),
                "tokens_used": snapshot.tokens_used,
                "max_tokens": snapshot.max_tokens,
                "usage_percentage": snapshot.usage_percentage * 100,
                "task_file": snapshot.task_file,
                "task_progress": snapshot.task_progress * 100
            }
            for snapshot in self.snapshots
        ]
