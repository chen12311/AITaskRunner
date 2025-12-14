"""
Google Gemini CLI Adapter Tests
测试 Gemini 适配器
"""
import pytest
from unittest.mock import patch

from core.cli_adapters.gemini import GeminiAdapter
from core.cli_adapters.base import CLIType


class TestGeminiAdapter:
    """测试 Gemini 适配器"""

    def test_adapter_name(self):
        """测试适配器名称"""
        adapter = GeminiAdapter()
        assert adapter.name == "Google Gemini CLI"

    def test_adapter_cli_type(self):
        """测试 CLI 类型"""
        adapter = GeminiAdapter()
        assert adapter.cli_type == CLIType.GEMINI

    def test_config_command(self):
        """测试配置命令"""
        adapter = GeminiAdapter()
        config = adapter.config
        assert config.cli_type == CLIType.GEMINI
        assert config.auto_approve_flag == "--approval-mode auto_edit"
        assert config.clear_command == "/clear"
        assert config.status_command is None
        assert config.resume_flag == "--resume"

    def test_get_start_command(self):
        """测试启动命令构建"""
        adapter = GeminiAdapter()
        cmd = adapter.get_start_command()
        assert "--approval-mode auto_edit" in cmd

    def test_get_start_command_with_prompt(self):
        """测试带提示的启动命令"""
        adapter = GeminiAdapter()
        cmd = adapter.get_start_command_with_prompt("Implement feature X")
        assert "--approval-mode auto_edit" in cmd
        assert "-p" in cmd
        assert "Implement feature X" in cmd

    def test_get_start_command_with_prompt_escape_quotes(self):
        """测试带引号的提示词转义"""
        adapter = GeminiAdapter()
        cmd = adapter.get_start_command_with_prompt('Fix the "bug"')
        assert '\\"bug\\"' in cmd

    def test_get_clear_session_command(self):
        """测试清空会话命令"""
        adapter = GeminiAdapter()
        assert adapter.get_clear_session_command() == "/clear"

    def test_supports_status_check(self):
        """测试不支持状态查询"""
        adapter = GeminiAdapter()
        assert adapter.supports_status_check() is False

    def test_supports_session_resume(self):
        """测试支持会话恢复"""
        adapter = GeminiAdapter()
        assert adapter.supports_session_resume() is True

    def test_get_resume_command(self):
        """测试恢复命令"""
        adapter = GeminiAdapter()
        cmd = adapter.get_resume_command()
        assert "--resume" in cmd

    @patch("shutil.which")
    def test_is_available_true(self, mock_which):
        """测试 CLI 可用"""
        mock_which.return_value = "/usr/local/bin/gemini"
        adapter = GeminiAdapter()
        assert adapter.is_available() is True

    @patch("shutil.which")
    def test_is_available_false(self, mock_which):
        """测试 CLI 不可用"""
        mock_which.return_value = None
        adapter = GeminiAdapter()
        assert adapter.is_available() is False

    def test_format_initial_prompt(self):
        """测试提示词格式化（透传）"""
        adapter = GeminiAdapter()
        prompt = "Test prompt"
        assert adapter.format_initial_prompt(prompt) == prompt


class TestGeminiAdapterAsync:
    """测试 Gemini 适配器异步方法"""

    @pytest.mark.asyncio
    async def test_get_status_default(self):
        """测试默认状态（假设运行中）"""
        adapter = GeminiAdapter()
        status = await adapter.get_status()

        assert status.is_running is True
        assert status.session_id is None
        assert status.context_tokens == 0
        assert status.max_tokens == 1000000  # Gemini 2.0 支持 100万 token
        assert "note" in status.extra_info
