"""
CLI Adapters __init__ Tests
测试 CLI 适配器模块初始化
"""
import pytest
from unittest.mock import patch, MagicMock

from core.cli_adapters import (
    get_cli_adapter,
    get_available_cli_types,
    CLIAdapter,
    CLIConfig,
    CLIStatus,
    CLIType,
    ClaudeCodeAdapter,
    CodexAdapter,
    GeminiAdapter,
)


class TestGetCliAdapter:
    """测试 get_cli_adapter 函数"""

    def test_get_claude_code_adapter(self):
        """测试获取 Claude Code 适配器"""
        adapter = get_cli_adapter("claude_code")
        assert isinstance(adapter, ClaudeCodeAdapter)

    def test_get_codex_adapter(self):
        """测试获取 Codex 适配器"""
        adapter = get_cli_adapter("codex")
        assert isinstance(adapter, CodexAdapter)

    def test_get_gemini_adapter(self):
        """测试获取 Gemini 适配器"""
        adapter = get_cli_adapter("gemini")
        assert isinstance(adapter, GeminiAdapter)

    def test_get_invalid_adapter(self):
        """测试获取无效的适配器"""
        with pytest.raises(ValueError) as exc_info:
            get_cli_adapter("invalid_type")
        assert "不支持的 CLI 类型" in str(exc_info.value)


class TestGetAvailableCliTypes:
    """测试 get_available_cli_types 函数"""

    def test_get_available_cli_types_all_available(self):
        """测试所有 CLI 都可用时"""
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True
        mock_adapter.name = "MockCLI"
        mock_adapter.supports_status_check.return_value = True
        mock_adapter.supports_session_resume.return_value = False

        with patch('core.cli_adapters.get_cli_adapter', return_value=mock_adapter):
            available = get_available_cli_types()
            assert len(available) == 3
            for item in available:
                assert "type" in item
                assert "name" in item
                assert "supports_status" in item
                assert "supports_resume" in item

    def test_get_available_cli_types_none_available(self):
        """测试没有 CLI 可用时"""
        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = False

        with patch('core.cli_adapters.get_cli_adapter', return_value=mock_adapter):
            available = get_available_cli_types()
            assert len(available) == 0

    def test_get_available_cli_types_with_exception(self):
        """测试获取适配器时发生异常"""
        with patch('core.cli_adapters.get_cli_adapter', side_effect=Exception("Test error")):
            available = get_available_cli_types()
            assert len(available) == 0

    def test_get_available_cli_types_partial_available(self):
        """测试部分 CLI 可用时"""
        call_count = [0]

        def mock_get_adapter(cli_type):
            call_count[0] += 1
            mock = MagicMock()
            # 只有第一个可用
            mock.is_available.return_value = (call_count[0] == 1)
            mock.name = f"Mock{cli_type}"
            mock.supports_status_check.return_value = True
            mock.supports_session_resume.return_value = False
            return mock

        with patch('core.cli_adapters.get_cli_adapter', side_effect=mock_get_adapter):
            available = get_available_cli_types()
            assert len(available) == 1


class TestModuleExports:
    """测试模块导出"""

    def test_cli_adapter_exported(self):
        """测试 CLIAdapter 已导出"""
        assert CLIAdapter is not None

    def test_cli_config_exported(self):
        """测试 CLIConfig 已导出"""
        assert CLIConfig is not None

    def test_cli_status_exported(self):
        """测试 CLIStatus 已导出"""
        assert CLIStatus is not None

    def test_cli_type_exported(self):
        """测试 CLIType 已导出"""
        assert CLIType is not None

    def test_claude_code_adapter_exported(self):
        """测试 ClaudeCodeAdapter 已导出"""
        assert ClaudeCodeAdapter is not None

    def test_codex_adapter_exported(self):
        """测试 CodexAdapter 已导出"""
        assert CodexAdapter is not None

    def test_gemini_adapter_exported(self):
        """测试 GeminiAdapter 已导出"""
        assert GeminiAdapter is not None
