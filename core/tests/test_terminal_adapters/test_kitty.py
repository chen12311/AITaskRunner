"""
Kitty Terminal Adapter Tests
测试 Kitty 适配器
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import os

from core.terminal_adapters.kitty import KittyAdapter
from core.terminal_adapters.base import TerminalSession


class TestKittyAdapter:
    """测试 Kitty 适配器"""

    def test_adapter_name(self):
        """测试适配器名称"""
        adapter = KittyAdapter()
        assert adapter.name == "Kitty"

    @patch("os.path.exists")
    def test_is_available_macos_app(self, mock_exists):
        """测试 macOS Kitty 应用可用"""
        def exists_side_effect(path):
            return path == "/Applications/kitty.app/Contents/MacOS/kitty"
        mock_exists.side_effect = exists_side_effect

        adapter = KittyAdapter()
        assert adapter.is_available() is True

    @patch("os.path.exists")
    def test_is_available_local_bin(self, mock_exists):
        """测试本地 bin Kitty 可用"""
        def exists_side_effect(path):
            return path == "/usr/local/bin/kitty"
        mock_exists.side_effect = exists_side_effect

        adapter = KittyAdapter()
        assert adapter.is_available() is True

    @patch("os.path.exists")
    @patch("os.popen")
    def test_is_available_in_path(self, mock_popen, mock_exists):
        """测试 PATH 中的 Kitty 可用"""
        mock_exists.return_value = False
        mock_popen.return_value.read.return_value = "/usr/bin/kitty\n"

        adapter = KittyAdapter()
        assert adapter.is_available() is True

    @patch("os.path.exists")
    @patch("os.popen")
    def test_is_not_available(self, mock_popen, mock_exists):
        """测试 Kitty 不可用"""
        mock_exists.return_value = False
        mock_popen.return_value.read.return_value = ""

        adapter = KittyAdapter()
        assert adapter.is_available() is False

    def test_get_kitty_path_default(self):
        """测试获取 Kitty 路径（默认）"""
        with patch("os.path.exists", return_value=False):
            adapter = KittyAdapter()
            path = adapter._get_kitty_path()
            assert path == "kitty"

    @patch("os.path.exists")
    def test_get_kitty_path_macos(self, mock_exists):
        """测试获取 macOS Kitty 路径"""
        def exists_side_effect(path):
            return path == "/Applications/kitty.app/Contents/MacOS/kitty"
        mock_exists.side_effect = exists_side_effect

        adapter = KittyAdapter()
        path = adapter._get_kitty_path()
        assert path == "/Applications/kitty.app/Contents/MacOS/kitty"

    def test_has_active_session_false(self):
        """测试无活跃会话"""
        adapter = KittyAdapter()
        assert adapter.has_active_session() is False

    def test_has_active_session_true(self):
        """测试有活跃会话"""
        adapter = KittyAdapter()
        adapter.current_session = TerminalSession(
            session_id="test",
            socket_path="/tmp/kitty-test"
        )
        assert adapter.has_active_session() is True


class TestKittyAdapterAsync:
    """测试 Kitty 适配器异步方法"""

    @pytest.mark.asyncio
    async def test_create_window_success(self):
        """测试成功创建窗口"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("os.path.exists", return_value=True):
                with patch("asyncio.sleep", return_value=None):
                    adapter = KittyAdapter()
                    session = await adapter.create_window(
                        project_dir="/tmp/project",
                        command="claude --dangerously-skip-permissions"
                    )

                    assert session is not None
                    assert session.socket_path is not None
                    assert adapter.current_session is not None

    @pytest.mark.asyncio
    async def test_create_window_with_env_vars(self):
        """测试带环境变量创建窗口"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            with patch("os.path.exists", return_value=True):
                with patch("asyncio.sleep", return_value=None):
                    adapter = KittyAdapter()
                    session = await adapter.create_window(
                        project_dir="/tmp/project",
                        command="claude",
                        task_id="task_123",
                        api_base_url="http://localhost:8086"
                    )

                    assert session is not None
                    # 验证 kitty 被调用
                    mock_exec.assert_called()

    @pytest.mark.asyncio
    async def test_send_text_no_session(self):
        """测试无会话时发送文本"""
        adapter = KittyAdapter()
        result = await adapter.send_text("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_text_success(self):
        """测试成功发送文本"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("os.path.exists", return_value=True):
                with patch("asyncio.sleep", return_value=None):
                    adapter = KittyAdapter()
                    adapter.current_session = TerminalSession(
                        session_id="test",
                        socket_path="/tmp/kitty-test"
                    )

                    result = await adapter.send_text("test message")
                    assert result is True

    @pytest.mark.asyncio
    async def test_send_text_failure(self):
        """测试发送文本失败"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b'', b'Error'))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = KittyAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                socket_path="/tmp/kitty-test"
            )

            result = await adapter.send_text("test message")
            assert result is False

    @pytest.mark.asyncio
    async def test_close_window_no_session(self):
        """测试无会话时关闭窗口"""
        adapter = KittyAdapter()
        result = await adapter.close_window()
        assert result is True

    @pytest.mark.asyncio
    async def test_close_window_success(self):
        """测试成功关闭窗口"""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("os.path.exists", return_value=True):
                with patch("os.remove"):
                    adapter = KittyAdapter()
                    adapter.current_session = TerminalSession(
                        session_id="test",
                        socket_path="/tmp/kitty-test"
                    )

                    result = await adapter.close_window()
                    assert result is True
                    assert adapter.current_session is None


class TestKittyAdapterWindowAlive:
    """测试 Kitty 窗口存活检查"""

    def test_is_window_alive_no_session(self):
        """测试无会话时窗口不存活"""
        adapter = KittyAdapter()
        assert adapter.is_window_alive() is False

    def test_is_window_alive_no_socket_path(self):
        """测试无 socket 路径时窗口不存活"""
        adapter = KittyAdapter()
        adapter.current_session = TerminalSession(session_id="test")
        assert adapter.is_window_alive() is False

    @patch("os.path.exists")
    def test_is_window_alive_socket_not_exists(self, mock_exists):
        """测试 socket 文件不存在时窗口不存活"""
        mock_exists.return_value = False
        adapter = KittyAdapter()
        adapter.current_session = TerminalSession(
            session_id="test",
            socket_path="/tmp/kitty-test"
        )
        assert adapter.is_window_alive() is False
