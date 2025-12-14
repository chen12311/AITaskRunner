"""
Context Manager Tests
测试上下文管理器
"""
import pytest
from datetime import datetime, timedelta

from core.context_manager import ContextManager, ContextWindow, ContextSnapshot


class TestContextSnapshot:
    """测试 ContextSnapshot"""

    def test_create_snapshot(self):
        """测试创建快照"""
        now = datetime.now()
        snapshot = ContextSnapshot(
            timestamp=now,
            tokens_used=50000,
            max_tokens=200000,
            usage_percentage=0.25,
            task_file="/tmp/task.md",
            task_progress=0.5
        )

        assert snapshot.timestamp == now
        assert snapshot.tokens_used == 50000
        assert snapshot.max_tokens == 200000
        assert snapshot.usage_percentage == 0.25
        assert snapshot.task_file == "/tmp/task.md"
        assert snapshot.task_progress == 0.5


class TestContextWindow:
    """测试 ContextWindow"""

    def test_default_init(self):
        """测试默认初始化"""
        window = ContextWindow()

        assert window.current_tokens == 0
        assert window.max_tokens == 200000
        assert window.threshold == 0.8
        assert window.history == []

    def test_custom_init(self):
        """测试自定义初始化"""
        window = ContextWindow(
            current_tokens=10000,
            max_tokens=100000,
            threshold=0.9
        )

        assert window.current_tokens == 10000
        assert window.max_tokens == 100000
        assert window.threshold == 0.9

    def test_usage_percentage(self):
        """测试使用百分比计算"""
        window = ContextWindow(current_tokens=50000, max_tokens=200000)
        assert window.usage_percentage == 0.25

    def test_usage_percentage_zero_max(self):
        """测试最大token为0时的使用百分比"""
        window = ContextWindow(current_tokens=0, max_tokens=0)
        assert window.usage_percentage == 0.0

    def test_usage_percentage_full(self):
        """测试100%使用率"""
        window = ContextWindow(current_tokens=200000, max_tokens=200000)
        assert window.usage_percentage == 1.0

    def test_should_restart_below_threshold(self):
        """测试低于阈值不需要重启"""
        window = ContextWindow(
            current_tokens=100000,
            max_tokens=200000,
            threshold=0.8
        )
        assert window.should_restart is False

    def test_should_restart_at_threshold(self):
        """测试达到阈值需要重启"""
        window = ContextWindow(
            current_tokens=160000,
            max_tokens=200000,
            threshold=0.8
        )
        assert window.should_restart is True

    def test_should_restart_above_threshold(self):
        """测试超过阈值需要重启"""
        window = ContextWindow(
            current_tokens=180000,
            max_tokens=200000,
            threshold=0.8
        )
        assert window.should_restart is True

    def test_available_tokens(self):
        """测试可用token数"""
        window = ContextWindow(current_tokens=50000, max_tokens=200000)
        assert window.available_tokens == 150000

    def test_available_tokens_full(self):
        """测试满额时可用token为0"""
        window = ContextWindow(current_tokens=200000, max_tokens=200000)
        assert window.available_tokens == 0


class TestContextManager:
    """测试 ContextManager"""

    def test_default_init(self):
        """测试默认初始化"""
        manager = ContextManager()

        assert manager.context_window.max_tokens == 200000
        assert manager.context_window.threshold == 0.8
        assert manager.context_window.current_tokens == 0
        assert manager.snapshots == []

    def test_custom_init(self):
        """测试自定义初始化"""
        manager = ContextManager(max_tokens=100000, threshold=0.9)

        assert manager.context_window.max_tokens == 100000
        assert manager.context_window.threshold == 0.9

    def test_update_context(self):
        """测试更新上下文"""
        manager = ContextManager()

        manager.update_context(
            current_tokens=50000,
            task_file="/tmp/task.md",
            task_progress=0.5
        )

        assert manager.context_window.current_tokens == 50000
        assert len(manager.snapshots) == 1
        assert manager.snapshots[0].tokens_used == 50000
        assert manager.snapshots[0].task_file == "/tmp/task.md"
        assert manager.snapshots[0].task_progress == 0.5

    def test_update_context_multiple_times(self):
        """测试多次更新上下文"""
        manager = ContextManager()

        manager.update_context(current_tokens=10000, task_file="task1.md", task_progress=0.1)
        manager.update_context(current_tokens=30000, task_file="task1.md", task_progress=0.3)
        manager.update_context(current_tokens=60000, task_file="task1.md", task_progress=0.6)

        assert manager.context_window.current_tokens == 60000
        assert len(manager.snapshots) == 3
        assert len(manager.context_window.history) == 3

    def test_check_threshold_false(self):
        """测试检查阈值（未达到）"""
        manager = ContextManager(max_tokens=200000, threshold=0.8)
        manager.update_context(current_tokens=100000)

        assert manager.check_threshold() is False

    def test_check_threshold_true(self):
        """测试检查阈值（已达到）"""
        manager = ContextManager(max_tokens=200000, threshold=0.8)
        manager.update_context(current_tokens=180000)

        assert manager.check_threshold() is True

    def test_get_usage_stats(self):
        """测试获取使用统计"""
        manager = ContextManager(max_tokens=200000, threshold=0.8)
        manager.update_context(current_tokens=50000, task_file="task.md", task_progress=0.5)

        stats = manager.get_usage_stats()

        assert stats["current_tokens"] == 50000
        assert stats["max_tokens"] == 200000
        assert stats["usage_percentage"] == 25.0  # 50000/200000 * 100
        assert stats["available_tokens"] == 150000
        assert stats["should_restart"] is False
        assert stats["total_snapshots"] == 1

    def test_get_usage_stats_should_restart(self):
        """测试获取使用统计（需要重启）"""
        manager = ContextManager(max_tokens=200000, threshold=0.8)
        manager.update_context(current_tokens=180000)

        stats = manager.get_usage_stats()

        assert stats["should_restart"] is True
        assert stats["usage_percentage"] == 90.0

    def test_reset_context(self):
        """测试重置上下文"""
        manager = ContextManager()
        manager.update_context(current_tokens=100000)

        assert manager.context_window.current_tokens == 100000

        manager.reset_context()

        assert manager.context_window.current_tokens == 0
        # 快照不应被清除
        assert len(manager.snapshots) == 1

    def test_get_recent_snapshots_less_than_count(self):
        """测试获取最近快照（少于请求数量）"""
        manager = ContextManager()
        manager.update_context(current_tokens=10000)
        manager.update_context(current_tokens=20000)
        manager.update_context(current_tokens=30000)

        recent = manager.get_recent_snapshots(count=10)

        assert len(recent) == 3

    def test_get_recent_snapshots_more_than_count(self):
        """测试获取最近快照（多于请求数量）"""
        manager = ContextManager()
        for i in range(15):
            manager.update_context(current_tokens=i * 10000)

        recent = manager.get_recent_snapshots(count=5)

        assert len(recent) == 5
        # 应该是最后5个
        assert recent[0].tokens_used == 100000
        assert recent[-1].tokens_used == 140000

    def test_get_recent_snapshots_empty(self):
        """测试获取最近快照（无快照）"""
        manager = ContextManager()
        recent = manager.get_recent_snapshots(count=10)

        assert recent == []

    def test_export_history_empty(self):
        """测试导出空历史"""
        manager = ContextManager()
        history = manager.export_history()

        assert history == []

    def test_export_history(self):
        """测试导出历史"""
        manager = ContextManager(max_tokens=200000)
        manager.update_context(current_tokens=50000, task_file="task.md", task_progress=0.5)

        history = manager.export_history()

        assert len(history) == 1
        assert history[0]["tokens_used"] == 50000
        assert history[0]["max_tokens"] == 200000
        assert history[0]["usage_percentage"] == 25.0  # 50000/200000 * 100
        assert history[0]["task_file"] == "task.md"
        assert history[0]["task_progress"] == 50.0  # 0.5 * 100
        assert "timestamp" in history[0]

    def test_export_history_multiple(self):
        """测试导出多条历史"""
        manager = ContextManager(max_tokens=100000)
        manager.update_context(current_tokens=20000, task_file="task1.md", task_progress=0.2)
        manager.update_context(current_tokens=40000, task_file="task1.md", task_progress=0.4)
        manager.update_context(current_tokens=80000, task_file="task1.md", task_progress=0.8)

        history = manager.export_history()

        assert len(history) == 3
        assert history[0]["tokens_used"] == 20000
        assert history[1]["tokens_used"] == 40000
        assert history[2]["tokens_used"] == 80000
        assert history[0]["usage_percentage"] == 20.0
        assert history[1]["usage_percentage"] == 40.0
        assert history[2]["usage_percentage"] == 80.0


class TestContextManagerEdgeCases:
    """测试边界情况"""

    def test_zero_max_tokens(self):
        """测试最大token为0"""
        manager = ContextManager(max_tokens=0)

        assert manager.context_window.usage_percentage == 0.0
        assert manager.context_window.available_tokens == 0
        assert manager.check_threshold() is False

    def test_threshold_at_zero(self):
        """测试阈值为0"""
        manager = ContextManager(threshold=0.0)

        # 任何使用都会触发重启
        assert manager.check_threshold() is True

    def test_threshold_at_one(self):
        """测试阈值为1"""
        manager = ContextManager(max_tokens=100000, threshold=1.0)
        manager.update_context(current_tokens=99999)

        assert manager.check_threshold() is False

        manager.update_context(current_tokens=100000)
        assert manager.check_threshold() is True

    def test_update_context_without_task_info(self):
        """测试不带任务信息的更新"""
        manager = ContextManager()
        manager.update_context(current_tokens=50000)

        assert manager.snapshots[0].task_file == ""
        assert manager.snapshots[0].task_progress == 0.0

    def test_snapshot_timestamp(self):
        """测试快照时间戳"""
        manager = ContextManager()

        before = datetime.now()
        manager.update_context(current_tokens=10000)
        after = datetime.now()

        snapshot = manager.snapshots[0]
        assert before <= snapshot.timestamp <= after
