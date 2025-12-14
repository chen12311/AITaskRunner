"""
OpenAI Codex CLI Adapter Tests
测试 Codex 适配器
"""
import pytest
from unittest.mock import patch

from core.cli_adapters.codex import CodexAdapter
from core.cli_adapters.base import CLIType


class TestCodexAdapter:
    """测试 Codex 适配器"""

    def test_adapter_name(self):
        """测试适配器名称"""
        adapter = CodexAdapter()
        assert adapter.name == "OpenAI Codex CLI"

    def test_adapter_cli_type(self):
        """测试 CLI 类型"""
        adapter = CodexAdapter()
        assert adapter.cli_type == CLIType.CODEX

    def test_config_command(self):
        """测试配置命令"""
        adapter = CodexAdapter()
        config = adapter.config
        assert config.cli_type == CLIType.CODEX
        assert config.auto_approve_flag == "--full-auto"
        assert config.clear_command is None
        assert config.status_command is None
        assert config.resume_flag == "resume --last"

    def test_get_start_command(self):
        """测试启动命令构建"""
        adapter = CodexAdapter()
        cmd = adapter.get_start_command()
        assert "--full-auto" in cmd

    def test_get_start_command_with_prompt(self):
        """测试带提示的启动命令"""
        adapter = CodexAdapter()
        cmd = adapter.get_start_command_with_prompt("Write a hello world function")
        assert "--full-auto" in cmd
        assert "Write a hello world function" in cmd

    def test_get_start_command_with_prompt_escape_quotes(self):
        """测试带引号的提示词转义"""
        adapter = CodexAdapter()
        cmd = adapter.get_start_command_with_prompt('Fix the "error" in code')
        assert '\\"error\\"' in cmd

    def test_get_clear_session_command(self):
        """测试清空会话命令（不支持）"""
        adapter = CodexAdapter()
        assert adapter.get_clear_session_command() is None

    def test_supports_status_check(self):
        """测试不支持状态查询"""
        adapter = CodexAdapter()
        assert adapter.supports_status_check() is False

    def test_supports_session_resume(self):
        """测试支持会话恢复"""
        adapter = CodexAdapter()
        assert adapter.supports_session_resume() is True

    def test_get_resume_command(self):
        """测试恢复命令"""
        adapter = CodexAdapter()
        cmd = adapter.get_resume_command()
        assert "resume --last" in cmd

    @patch("shutil.which")
    def test_is_available_true(self, mock_which):
        """测试 CLI 可用"""
        mock_which.return_value = "/usr/local/bin/codex"
        adapter = CodexAdapter()
        assert adapter.is_available() is True

    @patch("shutil.which")
    def test_is_available_false(self, mock_which):
        """测试 CLI 不可用"""
        mock_which.return_value = None
        adapter = CodexAdapter()
        assert adapter.is_available() is False

    def test_format_initial_prompt(self):
        """测试提示词格式化（透传）"""
        adapter = CodexAdapter()
        prompt = "Test prompt"
        assert adapter.format_initial_prompt(prompt) == prompt


class TestCodexAdapterAsync:
    """测试 Codex 适配器异步方法"""

    @pytest.mark.asyncio
    async def test_get_status_default(self):
        """测试默认状态（假设运行中）"""
        adapter = CodexAdapter()
        status = await adapter.get_status()

        assert status.is_running is True
        assert status.session_id is None
        assert status.context_tokens == 0
        assert status.max_tokens == 128000
        assert "note" in status.extra_info
