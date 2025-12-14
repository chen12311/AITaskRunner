"""
Settings Service Tests
测试设置服务
"""
import pytest
from unittest.mock import patch

from backend.services.settings_service import SettingsService


class TestSettingsService:
    """测试 SettingsService"""

    @pytest.mark.asyncio
    async def test_initialize(self, test_database):
        """测试初始化"""
        service = SettingsService(db=test_database)
        await service.initialize()

        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_get_setting_default(self, test_database):
        """测试获取默认设置"""
        service = SettingsService(db=test_database)

        terminal = await service.get_setting("terminal")
        assert terminal == "auto"

        cli = await service.get_setting("default_cli")
        assert cli == "claude_code"

    @pytest.mark.asyncio
    async def test_set_and_get_setting(self, test_database):
        """测试设置和获取配置"""
        service = SettingsService(db=test_database)

        success = await service.set_setting("language", "en")
        assert success is True

        value = await service.get_setting("language")
        assert value == "en"

    @pytest.mark.asyncio
    async def test_get_all_settings(self, test_database):
        """测试获取所有设置"""
        service = SettingsService(db=test_database)

        settings = await service.get_all_settings()

        assert "terminal" in settings
        assert "default_cli" in settings
        assert "language" in settings

        # 检查设置格式
        assert "value" in settings["terminal"]
        assert "description" in settings["terminal"]

    @pytest.mark.asyncio
    async def test_get_terminal_type(self, test_database):
        """测试获取终端类型"""
        service = SettingsService(db=test_database)

        terminal = await service.get_terminal_type()
        assert terminal == "auto"

    @pytest.mark.asyncio
    async def test_set_terminal_type_valid(self, test_database):
        """测试设置有效终端类型"""
        service = SettingsService(db=test_database)

        with patch("platform.system", return_value="Darwin"):
            success = await service.set_terminal_type("kitty")
            assert success is True

            terminal = await service.get_terminal_type()
            assert terminal == "kitty"

    @pytest.mark.asyncio
    async def test_set_terminal_type_invalid(self, test_database):
        """测试设置无效终端类型"""
        service = SettingsService(db=test_database)

        with patch("platform.system", return_value="Darwin"):
            with pytest.raises(ValueError) as exc_info:
                await service.set_terminal_type("invalid_terminal")

            assert "不支持的终端类型" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_cli_type(self, test_database):
        """测试获取 CLI 类型"""
        service = SettingsService(db=test_database)

        cli_type = await service.get_cli_type()
        assert cli_type == "claude_code"

    @pytest.mark.asyncio
    async def test_set_cli_type_valid(self, test_database):
        """测试设置有效 CLI 类型"""
        service = SettingsService(db=test_database)

        success = await service.set_cli_type("codex")
        assert success is True

        cli_type = await service.get_cli_type()
        assert cli_type == "codex"

    @pytest.mark.asyncio
    async def test_set_cli_type_invalid(self, test_database):
        """测试设置无效 CLI 类型"""
        service = SettingsService(db=test_database)

        with pytest.raises(ValueError) as exc_info:
            await service.set_cli_type("invalid_cli")

        assert "不支持的 CLI 类型" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_review_enabled_default(self, test_database):
        """测试获取默认 Review 启用状态"""
        service = SettingsService(db=test_database)

        enabled = await service.get_review_enabled()
        assert enabled is False

    @pytest.mark.asyncio
    async def test_set_review_enabled(self, test_database):
        """测试设置 Review 启用状态"""
        service = SettingsService(db=test_database)

        success = await service.set_review_enabled(True)
        assert success is True

        enabled = await service.get_review_enabled()
        assert enabled is True

    @pytest.mark.asyncio
    async def test_get_max_concurrent_sessions_default(self, test_database):
        """测试获取默认最大并发会话数"""
        service = SettingsService(db=test_database)

        max_sessions = await service.get_max_concurrent_sessions()
        assert max_sessions == 3

    @pytest.mark.asyncio
    async def test_set_max_concurrent_sessions_valid(self, test_database):
        """测试设置有效最大并发会话数"""
        service = SettingsService(db=test_database)

        success = await service.set_max_concurrent_sessions(5)
        assert success is True

        max_sessions = await service.get_max_concurrent_sessions()
        assert max_sessions == 5

    @pytest.mark.asyncio
    async def test_set_max_concurrent_sessions_too_low(self, test_database):
        """测试设置过低的最大并发会话数"""
        service = SettingsService(db=test_database)

        with pytest.raises(ValueError) as exc_info:
            await service.set_max_concurrent_sessions(0)

        assert "必须 >= 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_max_concurrent_sessions_too_high(self, test_database):
        """测试设置过高的最大并发会话数"""
        service = SettingsService(db=test_database)

        with pytest.raises(ValueError) as exc_info:
            await service.set_max_concurrent_sessions(15)

        assert "不能超过 10" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_language_default(self, test_database):
        """测试获取默认语言"""
        service = SettingsService(db=test_database)

        language = await service.get_language()
        assert language == "zh"

    @pytest.mark.asyncio
    async def test_set_language_valid(self, test_database):
        """测试设置有效语言"""
        service = SettingsService(db=test_database)

        success = await service.set_language("en")
        assert success is True

        language = await service.get_language()
        assert language == "en"

    @pytest.mark.asyncio
    async def test_set_language_invalid(self, test_database):
        """测试设置无效语言"""
        service = SettingsService(db=test_database)

        with pytest.raises(ValueError) as exc_info:
            await service.set_language("fr")

        assert "不支持的语言" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_watchdog_settings(self, test_database):
        """测试获取看门狗设置"""
        service = SettingsService(db=test_database)

        timeout = await service.get_watchdog_heartbeat_timeout()
        assert timeout == 300.0

        interval = await service.get_watchdog_check_interval()
        assert interval == 30.0

    @pytest.mark.asyncio
    async def test_set_watchdog_heartbeat_timeout_valid(self, test_database):
        """测试设置有效看门狗超时"""
        service = SettingsService(db=test_database)

        success = await service.set_watchdog_heartbeat_timeout(600)
        assert success is True

        timeout = await service.get_watchdog_heartbeat_timeout()
        assert timeout == 600.0

    @pytest.mark.asyncio
    async def test_set_watchdog_heartbeat_timeout_too_low(self, test_database):
        """测试设置过低的看门狗超时"""
        service = SettingsService(db=test_database)

        with pytest.raises(ValueError) as exc_info:
            await service.set_watchdog_heartbeat_timeout(30)

        assert "不能小于 60 秒" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_watchdog_check_interval_valid(self, test_database):
        """测试设置有效看门狗检查间隔"""
        service = SettingsService(db=test_database)

        success = await service.set_watchdog_check_interval(60)
        assert success is True

        interval = await service.get_watchdog_check_interval()
        assert interval == 60.0

    @pytest.mark.asyncio
    async def test_get_supported_terminals(self, test_database):
        """测试获取支持的终端列表"""
        service = SettingsService(db=test_database)

        with patch("platform.system", return_value="Darwin"):
            terminals = await service.get_supported_terminals()
            assert "auto" in terminals
            assert "kitty" in terminals
            assert "iterm" in terminals

    @pytest.mark.asyncio
    async def test_get_review_cli_type(self, test_database):
        """测试获取 Review CLI 类型"""
        service = SettingsService(db=test_database)

        cli_type = await service.get_review_cli_type()
        assert cli_type == "codex"

    @pytest.mark.asyncio
    async def test_set_review_cli_type_valid(self, test_database):
        """测试设置有效 Review CLI 类型"""
        service = SettingsService(db=test_database)

        success = await service.set_review_cli_type("gemini")
        assert success is True

        cli_type = await service.get_review_cli_type()
        assert cli_type == "gemini"

    @pytest.mark.asyncio
    async def test_set_review_cli_type_invalid(self, test_database):
        """测试设置无效 Review CLI 类型"""
        service = SettingsService(db=test_database)

        with pytest.raises(ValueError):
            await service.set_review_cli_type("invalid")
