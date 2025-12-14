"""
iTerm Terminal Adapter Tests
测试 iTerm 适配器
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from core.terminal_adapters.iterm import iTermAdapter
from core.terminal_adapters.base import TerminalSession


class TestiTermAdapter:
    """测试 iTerm 适配器"""

    def test_adapter_name(self):
        """测试适配器名称"""
        adapter = iTermAdapter()
        assert adapter.name == "iTerm"

    @patch("os.path.exists")
    def test_is_available_true(self, mock_exists):
        """测试 iTerm 可用"""
        mock_exists.return_value = True
        adapter = iTermAdapter()
        assert adapter.is_available() is True

    @patch("os.path.exists")
    def test_is_available_false(self, mock_exists):
        """测试 iTerm 不可用"""
        mock_exists.return_value = False
        adapter = iTermAdapter()
        assert adapter.is_available() is False

    def test_has_active_session_false(self):
        """测试无活跃会话"""
        adapter = iTermAdapter()
        assert adapter.has_active_session() is False

    def test_has_active_session_true(self):
        """测试有活跃会话"""
        adapter = iTermAdapter()
        adapter.current_session = TerminalSession(session_id="test", window_id="123")
        assert adapter.has_active_session() is True

    def test_clear_session(self):
        """测试清除会话"""
        adapter = iTermAdapter()
        adapter.current_session = TerminalSession(session_id="test")
        adapter.clear_session()
        assert adapter.current_session is None


class TestiTermAdapterAsync:
    """测试 iTerm 适配器异步方法"""

    @pytest.mark.asyncio
    async def test_create_window_success(self):
        """测试成功创建窗口"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'12345', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.sleep", return_value=None):
                adapter = iTermAdapter()
                session = await adapter.create_window(
                    project_dir="/tmp/project",
                    command="claude --dangerously-skip-permissions"
                )

                assert session is not None
                assert session.window_id == "12345"
                assert adapter.current_session is not None

    @pytest.mark.asyncio
    async def test_create_window_with_env_vars(self):
        """测试带环境变量创建窗口"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'12345', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            with patch("asyncio.sleep", return_value=None):
                adapter = iTermAdapter()
                session = await adapter.create_window(
                    project_dir="/tmp/project",
                    command="claude",
                    task_id="task_123",
                    api_base_url="http://localhost:8086"
                )

                assert session is not None
                # 验证 osascript 被调用
                mock_exec.assert_called()

    @pytest.mark.asyncio
    async def test_create_window_failure(self):
        """测试创建窗口失败"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b'', b'Error'))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = iTermAdapter()
            session = await adapter.create_window(
                project_dir="/tmp/project",
                command="claude"
            )

            assert session is None

    @pytest.mark.asyncio
    async def test_create_window_timeout(self):
        """测试创建窗口超时"""
        mock_process = AsyncMock()
        mock_process.kill = MagicMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                adapter = iTermAdapter()
                session = await adapter.create_window(
                    project_dir="/tmp/project",
                    command="claude"
                )

                assert session is None

    @pytest.mark.asyncio
    async def test_send_text_no_session(self):
        """测试无会话时发送文本"""
        adapter = iTermAdapter()
        result = await adapter.send_text("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_close_window_no_session(self):
        """测试无会话时关闭窗口"""
        adapter = iTermAdapter()
        result = await adapter.close_window()
        assert result is True

    @pytest.mark.asyncio
    async def test_close_window_success(self):
        """测试成功关闭窗口"""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = iTermAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="12345"
            )

            result = await adapter.close_window()
            assert result is True
            assert adapter.current_session is None
