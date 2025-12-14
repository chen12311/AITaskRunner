"""
Session Models Tests
测试会话数据模型
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from core.session.models import ManagedSession, SessionStatus


class TestSessionStatus:
    """测试 SessionStatus 枚举"""

    def test_status_values(self):
        """测试状态值"""
        assert SessionStatus.IDLE.value == "idle"
        assert SessionStatus.STARTING.value == "starting"
        assert SessionStatus.RUNNING.value == "running"
        assert SessionStatus.STOPPING.value == "stopping"
        assert SessionStatus.STOPPED.value == "stopped"
        assert SessionStatus.ERROR.value == "error"

    def test_status_count(self):
        """测试状态数量"""
        assert len(SessionStatus) == 6


class TestManagedSession:
    """测试 ManagedSession 数据类"""

    def create_mock_session(self, status=SessionStatus.IDLE):
        """创建模拟会话"""
        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.is_window_alive.return_value = True
        mock_terminal.clear_session = MagicMock()

        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"

        return ManagedSession(
            task_id="task_123",
            monitor=None,
            terminal=mock_terminal,
            cli_adapter=mock_cli,
            status=status,
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            cli_type="claude_code",
            api_base_url="http://localhost:8086"
        )

    def test_session_creation(self):
        """测试会话创建"""
        session = self.create_mock_session()
        assert session.task_id == "task_123"
        assert session.status == SessionStatus.IDLE
        assert session.project_dir == "/tmp/project"
        assert session.cli_type == "claude_code"
        assert session.semaphore_acquired is False

    def test_to_dict(self):
        """测试转换为字典"""
        session = self.create_mock_session()
        result = session.to_dict()

        assert result["task_id"] == "task_123"
        assert result["status"] == "idle"
        assert result["project_dir"] == "/tmp/project"
        assert result["terminal_name"] == "MockTerminal"
        assert result["cli_name"] == "MockCLI"

    def test_is_active_idle(self):
        """测试空闲状态不活跃"""
        session = self.create_mock_session(SessionStatus.IDLE)
        assert session.is_active() is False

    def test_is_active_starting(self):
        """测试启动中状态活跃"""
        session = self.create_mock_session(SessionStatus.STARTING)
        assert session.is_active() is True

    def test_is_active_running(self):
        """测试运行中状态活跃"""
        session = self.create_mock_session(SessionStatus.RUNNING)
        assert session.is_active() is True

    def test_is_active_stopped(self):
        """测试已停止状态不活跃"""
        session = self.create_mock_session(SessionStatus.STOPPED)
        assert session.is_active() is False

    def test_is_terminal_stopped(self):
        """测试已停止是终止状态"""
        session = self.create_mock_session(SessionStatus.STOPPED)
        assert session.is_terminal() is True

    def test_is_terminal_error(self):
        """测试错误是终止状态"""
        session = self.create_mock_session(SessionStatus.ERROR)
        assert session.is_terminal() is True

    def test_is_terminal_running(self):
        """测试运行中不是终止状态"""
        session = self.create_mock_session(SessionStatus.RUNNING)
        assert session.is_terminal() is False

    def test_mark_starting(self):
        """测试标记启动中"""
        session = self.create_mock_session()
        session.mark_starting()
        assert session.status == SessionStatus.STARTING
        assert session.started_at is not None

    def test_mark_running(self):
        """测试标记运行中"""
        session = self.create_mock_session()
        session.mark_running()
        assert session.status == SessionStatus.RUNNING

    def test_mark_stopping(self):
        """测试标记停止中"""
        session = self.create_mock_session()
        session.mark_stopping()
        assert session.status == SessionStatus.STOPPING

    def test_mark_stopped(self):
        """测试标记已停止"""
        session = self.create_mock_session()
        session.mark_stopped()
        assert session.status == SessionStatus.STOPPED
        assert session.stopped_at is not None

    def test_mark_error(self):
        """测试标记错误"""
        session = self.create_mock_session()
        session.mark_error("Test error message")
        assert session.status == SessionStatus.ERROR
        assert session.error_message == "Test error message"
        assert session.stopped_at is not None

    def test_verify_alive_not_active(self):
        """测试非活跃状态验证存活"""
        session = self.create_mock_session(SessionStatus.IDLE)
        assert session.verify_alive() is False

    def test_verify_alive_active_window_alive(self):
        """测试活跃状态且窗口存活"""
        session = self.create_mock_session(SessionStatus.RUNNING)
        session.terminal.is_window_alive.return_value = True
        assert session.verify_alive() is True

    def test_verify_alive_active_window_dead(self):
        """测试活跃状态但窗口已死（幽灵会话）"""
        session = self.create_mock_session(SessionStatus.RUNNING)
        session.terminal.is_window_alive.return_value = False

        result = session.verify_alive()

        assert result is False
        assert session.status == SessionStatus.STOPPED
        session.terminal.clear_session.assert_called_once()
