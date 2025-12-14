"""
Windows Terminal Adapter Tests
测试 Windows Terminal 适配器
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import subprocess

from core.terminal_adapters.windows_terminal import WindowsTerminalAdapter
from core.terminal_adapters.base import TerminalSession


class TestWindowsTerminalAdapter:
    """测试 Windows Terminal 适配器"""

    def test_adapter_name(self):
        """测试适配器名称"""
        adapter = WindowsTerminalAdapter()
        assert adapter.name == "Windows Terminal"

    def test_initial_state(self):
        """测试初始状态"""
        adapter = WindowsTerminalAdapter()
        assert adapter.current_session is None
        assert adapter._process_id is None

    @patch("subprocess.run")
    def test_is_available_wt_found(self, mock_run):
        """测试 wt.exe 可用"""
        mock_run.return_value = MagicMock(returncode=0)

        adapter = WindowsTerminalAdapter()
        assert adapter.is_available() is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_is_available_wt_not_found_where_found(self, mock_run):
        """测试 wt.exe 不可用但 where 找到"""
        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "wt.exe":
                raise FileNotFoundError()
            elif cmd[0] == "where":
                return MagicMock(returncode=0)
            return MagicMock(returncode=1)

        mock_run.side_effect = run_side_effect

        adapter = WindowsTerminalAdapter()
        assert adapter.is_available() is True

    @patch("subprocess.run")
    def test_is_available_not_found(self, mock_run):
        """测试 Windows Terminal 不可用"""
        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "wt.exe":
                raise FileNotFoundError()
            elif cmd[0] == "where":
                return MagicMock(returncode=1)
            return MagicMock(returncode=1)

        mock_run.side_effect = run_side_effect

        adapter = WindowsTerminalAdapter()
        assert adapter.is_available() is False

    @patch("subprocess.run")
    def test_is_available_timeout(self, mock_run):
        """测试 wt.exe 检测超时"""
        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "wt.exe":
                raise subprocess.TimeoutExpired(cmd="wt.exe", timeout=3)
            elif cmd[0] == "where":
                return MagicMock(returncode=0)
            return MagicMock(returncode=1)

        mock_run.side_effect = run_side_effect

        adapter = WindowsTerminalAdapter()
        assert adapter.is_available() is True

    def test_has_active_session_false(self):
        """测试无活跃会话"""
        adapter = WindowsTerminalAdapter()
        assert adapter.has_active_session() is False

    def test_has_active_session_true(self):
        """测试有活跃会话"""
        adapter = WindowsTerminalAdapter()
        adapter.current_session = TerminalSession(
            session_id="test",
            window_id="test-window"
        )
        assert adapter.has_active_session() is True


class TestWindowsTerminalAdapterAsync:
    """测试 Windows Terminal 适配器异步方法"""

    @pytest.mark.asyncio
    async def test_run_powershell_success(self):
        """测试 PowerShell 执行成功"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(b'output', b'')
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            success, stdout, stderr = await adapter._run_powershell("Write-Host 'test'")

            assert success is True
            assert stdout == "output"
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_run_powershell_failure(self):
        """测试 PowerShell 执行失败"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b'', b'error message')
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            success, stdout, stderr = await adapter._run_powershell("bad command")

            assert success is False
            assert stdout == ""
            assert stderr == "error message"

    @pytest.mark.asyncio
    async def test_run_powershell_timeout(self):
        """测试 PowerShell 执行超时"""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_process.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            success, stdout, stderr = await adapter._run_powershell("slow command")

            assert success is False
            assert stderr == "PowerShell 执行超时"
            mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_powershell_exception(self):
        """测试 PowerShell 执行异常"""
        with patch("asyncio.create_subprocess_exec", side_effect=Exception("subprocess error")):
            adapter = WindowsTerminalAdapter()
            success, stdout, stderr = await adapter._run_powershell("command")

            assert success is False
            assert stdout == ""
            assert "subprocess error" in stderr

    @pytest.mark.asyncio
    async def test_create_window_success(self):
        """测试成功创建窗口"""
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.sleep", return_value=None):
                adapter = WindowsTerminalAdapter()
                session = await adapter.create_window(
                    project_dir="C:\\Projects\\test",
                    command="claude --dangerously-skip-permissions"
                )

                assert session is not None
                assert adapter.current_session is not None
                assert adapter._process_id == 12345

    @pytest.mark.asyncio
    async def test_create_window_with_env_vars(self):
        """测试带环境变量创建窗口"""
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            with patch("asyncio.sleep", return_value=None):
                adapter = WindowsTerminalAdapter()
                session = await adapter.create_window(
                    project_dir="C:\\Projects\\test",
                    command="codex",
                    task_id="task_123",
                    api_base_url="http://localhost:8086"
                )

                assert session is not None
                assert session.session_id == "task_123"
                mock_exec.assert_called()

    @pytest.mark.asyncio
    async def test_create_window_failure(self):
        """测试创建窗口失败"""
        with patch("asyncio.create_subprocess_exec", side_effect=Exception("Failed to start")):
            adapter = WindowsTerminalAdapter()
            session = await adapter.create_window(
                project_dir="C:\\Projects\\test",
                command="claude"
            )

            assert session is None

    @pytest.mark.asyncio
    async def test_create_window_escapes_special_chars(self):
        """测试创建窗口时转义特殊字符"""
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            with patch("asyncio.sleep", return_value=None):
                adapter = WindowsTerminalAdapter()
                # 包含双引号的路径和命令
                session = await adapter.create_window(
                    project_dir='C:\\Projects\\"test"',
                    command='claude "hello"'
                )

                assert session is not None

    @pytest.mark.asyncio
    async def test_send_text_no_session(self):
        """测试无会话时发送文本"""
        adapter = WindowsTerminalAdapter()
        result = await adapter.send_text("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_text_success(self):
        """测试成功发送文本"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="test-window"
            )

            result = await adapter.send_text("test message")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_text_with_press_enter_false(self):
        """测试发送文本不按回车"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="test-window"
            )

            result = await adapter.send_text("test message", press_enter=False)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_text_clipboard_failure(self):
        """测试写入剪贴板失败"""
        call_count = 0

        async def mock_communicate():
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # 第一次调用：读取剪贴板
                return (b'saved', b'')
            elif call_count == 2:  # 第二次调用：写入剪贴板
                return (b'', b'clipboard error')
            return (b'', b'')

        mock_process = AsyncMock()
        mock_process.returncode = 1  # 失败
        mock_process.communicate = mock_communicate

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="test-window"
            )

            result = await adapter.send_text("test message")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_text_escapes_single_quotes(self):
        """测试发送文本时转义单引号"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="test-window"
            )

            # 包含单引号的文本
            result = await adapter.send_text("hello 'world'")
            assert result is True

    @pytest.mark.asyncio
    async def test_close_window_no_session(self):
        """测试无会话时关闭窗口"""
        adapter = WindowsTerminalAdapter()
        result = await adapter.close_window()
        assert result is True

    @pytest.mark.asyncio
    async def test_close_window_with_process_id(self):
        """测试有进程 ID 时关闭窗口"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="test-window"
            )
            adapter._process_id = 12345

            result = await adapter.close_window()
            assert result is True
            assert adapter.current_session is None
            assert adapter._process_id is None

    @pytest.mark.asyncio
    async def test_close_window_without_process_id(self):
        """测试无进程 ID 时关闭窗口（使用 Alt+F4）"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="test-window"
            )
            # 没有设置 _process_id

            result = await adapter.close_window()
            assert result is True
            assert adapter.current_session is None

    @pytest.mark.asyncio
    async def test_close_window_powershell_failure(self):
        """测试关闭窗口时 PowerShell 调用失败但仍清理会话"""
        # _run_powershell 内部捕获异常，所以 close_window 不会收到异常
        # 它会返回 True 并清理会话
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b'', b'error'))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = WindowsTerminalAdapter()
            adapter.current_session = TerminalSession(
                session_id="test",
                window_id="test-window"
            )
            adapter._process_id = 12345

            result = await adapter.close_window()
            # 即使 PowerShell 失败也会返回 True 并清理会话
            assert result is True
            assert adapter.current_session is None
            assert adapter._process_id is None



class TestWindowsTerminalAdapterWindowAlive:
    """测试 Windows Terminal 窗口存活检查"""

    def test_is_window_alive_no_session(self):
        """测试无会话时窗口不存活"""
        adapter = WindowsTerminalAdapter()
        assert adapter.is_window_alive() is False

    def test_is_window_alive_with_session(self):
        """测试有会话时窗口存活"""
        adapter = WindowsTerminalAdapter()
        adapter.current_session = TerminalSession(
            session_id="test",
            window_id="test-window"
        )
        # 默认实现：有会话就认为存活
        assert adapter.is_window_alive() is True
