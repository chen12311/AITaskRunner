"""
Claude Code CLI Adapter Tests
测试 Claude Code 适配器
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from core.cli_adapters.claude_code import ClaudeCodeAdapter
from core.cli_adapters.base import CLIType, CLIStatus


class TestClaudeCodeAdapter:
    """测试 Claude Code 适配器"""

    def test_adapter_name(self):
        """测试适配器名称"""
        adapter = ClaudeCodeAdapter()
        assert adapter.name == "Claude Code"

    def test_adapter_cli_type(self):
        """测试 CLI 类型"""
        adapter = ClaudeCodeAdapter()
        assert adapter.cli_type == CLIType.CLAUDE_CODE

    def test_config_command(self):
        """测试配置命令"""
        adapter = ClaudeCodeAdapter()
        config = adapter.config
        assert config.cli_type == CLIType.CLAUDE_CODE
        assert config.auto_approve_flag == "--dangerously-skip-permissions"
        assert config.clear_command == "/clear"
        assert config.status_command == "status --format json"
        assert config.resume_flag is None

    def test_get_start_command(self):
        """测试启动命令构建"""
        adapter = ClaudeCodeAdapter()
        cmd = adapter.get_start_command()
        assert "--dangerously-skip-permissions" in cmd

    def test_get_start_command_with_project_dir(self):
        """测试带项目目录的启动命令"""
        adapter = ClaudeCodeAdapter()
        cmd = adapter.get_start_command(project_dir="/tmp/project")
        # 项目目录参数当前未使用，但命令应正常生成
        assert "--dangerously-skip-permissions" in cmd

    def test_get_clear_session_command(self):
        """测试清空会话命令"""
        adapter = ClaudeCodeAdapter()
        assert adapter.get_clear_session_command() == "/clear"

    def test_supports_status_check(self):
        """测试支持状态查询"""
        adapter = ClaudeCodeAdapter()
        assert adapter.supports_status_check() is True

    def test_supports_session_resume(self):
        """测试不支持会话恢复"""
        adapter = ClaudeCodeAdapter()
        assert adapter.supports_session_resume() is False

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_is_available_with_path(self, mock_exists, mock_which):
        """测试 CLI 可用性检查（PATH 中存在）"""
        mock_exists.return_value = False
        mock_which.return_value = "/usr/local/bin/claude"

        adapter = ClaudeCodeAdapter()
        assert adapter.is_available() is True

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_is_available_with_user_path(self, mock_exists, mock_which):
        """测试 CLI 可用性检查（用户目录存在）"""
        mock_exists.return_value = True
        mock_which.return_value = None

        adapter = ClaudeCodeAdapter()
        assert adapter.is_available() is True

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_is_not_available(self, mock_exists, mock_which):
        """测试 CLI 不可用"""
        mock_exists.return_value = False
        mock_which.return_value = None

        adapter = ClaudeCodeAdapter()
        assert adapter.is_available() is False


class TestClaudeCodeAdapterAsync:
    """测试 Claude Code 适配器异步方法"""

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """测试成功获取状态"""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(
            b'{"session_id": "sess_123", "context_tokens": 50000, "max_context_tokens": 200000}',
            b''
        ))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = ClaudeCodeAdapter()
            status = await adapter.get_status()

            assert status.is_running is True
            assert status.session_id == "sess_123"
            assert status.context_tokens == 50000
            assert status.max_tokens == 200000
            assert status.context_usage == 0.25

    @pytest.mark.asyncio
    async def test_get_status_not_running(self):
        """测试 CLI 未运行"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b'', b''))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            adapter = ClaudeCodeAdapter()
            status = await adapter.get_status()

            assert status.is_running is False

    @pytest.mark.asyncio
    async def test_get_status_timeout(self):
        """测试状态查询超时"""
        mock_process = AsyncMock()
        mock_process.kill = MagicMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                adapter = ClaudeCodeAdapter()
                status = await adapter.get_status()

                assert status.is_running is False

    @pytest.mark.asyncio
    async def test_get_status_exception(self):
        """测试状态查询异常"""
        with patch("asyncio.create_subprocess_exec", side_effect=Exception("Test error")):
            adapter = ClaudeCodeAdapter()
            status = await adapter.get_status()

            assert status.is_running is False
