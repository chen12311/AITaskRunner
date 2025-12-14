"""
CLI Monitor Tests
测试 CLI 监控器
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from core.cli_monitor import CLIMonitor
from core.cli_adapters.base import CLIStatus


class TestCLIMonitorInit:
    """测试 CLIMonitor 初始化"""

    def test_init_default(self):
        """测试默认初始化"""
        monitor = CLIMonitor()

        assert monitor.context_threshold == 0.8
        assert monitor.session_active is False
        assert monitor.current_project_dir is None
        assert monitor.current_doc_path is None
        assert monitor.current_task_id is None
        assert monitor._cli_type == "claude_code"

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        mock_settings = MagicMock()
        mock_terminal = MagicMock()
        mock_cli = MagicMock()

        monitor = CLIMonitor(
            context_threshold=0.9,
            db_path="/tmp/test.db",
            settings_service=mock_settings,
            cli_type="codex",
            task_id="task_123",
            terminal_adapter=mock_terminal,
            cli_adapter=mock_cli
        )

        assert monitor.context_threshold == 0.9
        assert monitor._db_path == "/tmp/test.db"
        assert monitor._settings_service == mock_settings
        assert monitor._cli_type == "codex"
        assert monitor.current_task_id == "task_123"
        assert monitor._terminal == mock_terminal
        assert monitor._cli_adapter == mock_cli


class TestCLIMonitorAsync:
    """测试 CLIMonitor 异步方法"""

    @pytest.mark.asyncio
    async def test_initialize_with_external_adapters(self):
        """测试使用外部适配器初始化"""
        mock_terminal = MagicMock()
        mock_cli = MagicMock()

        monitor = CLIMonitor(
            terminal_adapter=mock_terminal,
            cli_adapter=mock_cli
        )

        await monitor.initialize()

        # 外部传入的适配器不应该被替换
        assert monitor._terminal == mock_terminal
        assert monitor._cli_adapter == mock_cli

    @pytest.mark.asyncio
    async def test_get_terminal_type_default(self):
        """测试获取默认终端类型"""
        monitor = CLIMonitor()
        terminal_type = await monitor._get_terminal_type()
        assert terminal_type == "auto"

    @pytest.mark.asyncio
    async def test_get_terminal_type_from_settings(self):
        """测试从设置获取终端类型"""
        mock_settings = MagicMock()
        mock_settings.get_terminal_type = AsyncMock(return_value="iterm")

        monitor = CLIMonitor(settings_service=mock_settings)
        terminal_type = await monitor._get_terminal_type()
        assert terminal_type == "iterm"

    @pytest.mark.asyncio
    async def test_get_cli_type_default(self):
        """测试获取默认 CLI 类型"""
        monitor = CLIMonitor(cli_type="gemini")
        cli_type = await monitor._get_cli_type()
        assert cli_type == "gemini"

    @pytest.mark.asyncio
    async def test_get_cli_type_from_settings(self):
        """测试从设置获取 CLI 类型"""
        mock_settings = MagicMock()
        mock_settings.get_cli_type = AsyncMock(return_value="codex")

        monitor = CLIMonitor(settings_service=mock_settings)
        cli_type = await monitor._get_cli_type()
        assert cli_type == "codex"


class TestCLIMonitorAdapters:
    """测试适配器管理"""

    def test_init_cli_adapter_success(self):
        """测试成功初始化 CLI 适配器"""
        monitor = CLIMonitor()

        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True
        mock_adapter.name = "MockCLI"

        with patch('core.cli_monitor.get_cli_adapter', return_value=mock_adapter):
            monitor._init_cli_adapter("claude_code")

        assert monitor._cli_adapter == mock_adapter

    def test_init_cli_adapter_unavailable(self):
        """测试 CLI 适配器不可用"""
        monitor = CLIMonitor()

        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = False
        mock_adapter.name = "MockCLI"

        with patch('core.cli_monitor.get_cli_adapter', return_value=mock_adapter):
            monitor._init_cli_adapter("claude_code")

        assert monitor._cli_adapter is None

    def test_init_cli_adapter_invalid_type(self):
        """测试无效的 CLI 类型"""
        monitor = CLIMonitor()

        with patch('core.cli_monitor.get_cli_adapter', side_effect=ValueError("Invalid type")):
            monitor._init_cli_adapter("invalid_type")

        assert monitor._cli_adapter is None

    @pytest.mark.asyncio
    async def test_update_cli_adapter(self):
        """测试更新 CLI 适配器"""
        monitor = CLIMonitor()

        mock_adapter = MagicMock()
        mock_adapter.is_available.return_value = True
        mock_adapter.name = "CodexCLI"

        with patch('core.cli_monitor.get_cli_adapter', return_value=mock_adapter):
            await monitor.update_cli_adapter("codex")

        assert monitor._cli_type == "codex"
        assert monitor._cli_adapter == mock_adapter

    @pytest.mark.asyncio
    async def test_init_terminal_adapter_kitty(self):
        """测试初始化 Kitty 终端适配器"""
        mock_settings = MagicMock()
        mock_settings.get_terminal_type = AsyncMock(return_value="kitty")

        monitor = CLIMonitor(settings_service=mock_settings)

        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = True

        with patch('core.cli_monitor.KittyAdapter', return_value=mock_kitty):
            await monitor._init_terminal_adapter()

        assert monitor._terminal == mock_kitty

    @pytest.mark.asyncio
    async def test_init_terminal_adapter_iterm(self):
        """测试初始化 iTerm 终端适配器"""
        mock_settings = MagicMock()
        mock_settings.get_terminal_type = AsyncMock(return_value="iterm")

        monitor = CLIMonitor(settings_service=mock_settings)

        mock_iterm = MagicMock()
        mock_iterm.is_available.return_value = True

        with patch('core.cli_monitor.iTermAdapter', return_value=mock_iterm):
            await monitor._init_terminal_adapter()

        assert monitor._terminal == mock_iterm

    @pytest.mark.asyncio
    async def test_init_terminal_adapter_auto(self):
        """测试自动检测终端适配器"""
        mock_settings = MagicMock()
        mock_settings.get_terminal_type = AsyncMock(return_value="auto")

        monitor = CLIMonitor(settings_service=mock_settings)

        mock_default = MagicMock()
        mock_default.name = "DefaultTerminal"

        with patch('core.cli_monitor.get_default_terminal_adapter', return_value=mock_default):
            await monitor._init_terminal_adapter()

        assert monitor._terminal == mock_default

    @pytest.mark.asyncio
    async def test_init_terminal_adapter_unsupported(self):
        """测试不支持的终端类型"""
        mock_settings = MagicMock()
        mock_settings.get_terminal_type = AsyncMock(return_value="unsupported")

        monitor = CLIMonitor(settings_service=mock_settings)
        await monitor._init_terminal_adapter()

        assert monitor._terminal is None


class TestCLIMonitorSession:
    """测试会话管理"""

    @pytest.mark.asyncio
    async def test_start_session_no_cli_adapter(self):
        """测试没有 CLI 适配器时启动失败"""
        mock_terminal = MagicMock()

        monitor = CLIMonitor(terminal_adapter=mock_terminal)
        monitor._cli_adapter = None

        result = await monitor.start_session(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_start_session_no_terminal_adapter(self):
        """测试没有终端适配器时启动失败"""
        mock_cli = MagicMock()

        monitor = CLIMonitor(cli_adapter=mock_cli)
        monitor._terminal = None

        result = await monitor.start_session(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_start_session_success(self):
        """测试成功启动会话"""
        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.create_window = AsyncMock(return_value={"session_id": "123"})
        mock_terminal.send_text = AsyncMock(return_value=True)

        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"
        mock_cli.get_start_command.return_value = "mock-cli start"
        mock_cli.get_clear_session_command.return_value = None
        mock_cli.format_initial_prompt.return_value = "formatted prompt"

        mock_template_service = MagicMock()
        mock_template_service.render_template_async = AsyncMock(return_value="initial task")

        monitor = CLIMonitor(
            terminal_adapter=mock_terminal,
            cli_adapter=mock_cli
        )
        monitor._template_service = mock_template_service

        result = await monitor.start_session(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123",
            api_base_url="http://localhost:8080"
        )

        assert result is True
        assert monitor.session_active is True
        assert monitor.current_project_dir == "/tmp/project"
        assert monitor.current_doc_path == "/tmp/project/TODO.md"
        assert monitor.current_task_id == "task_123"

    @pytest.mark.asyncio
    async def test_start_session_window_creation_failed(self):
        """测试窗口创建失败"""
        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.create_window = AsyncMock(return_value=None)

        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"
        mock_cli.get_start_command.return_value = "mock-cli start"

        mock_template_service = MagicMock()
        mock_template_service.render_template_async = AsyncMock(return_value="initial task")

        monitor = CLIMonitor(
            terminal_adapter=mock_terminal,
            cli_adapter=mock_cli
        )
        monitor._template_service = mock_template_service

        result = await monitor.start_session(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert result is False
        assert monitor.session_active is False

    @pytest.mark.asyncio
    async def test_send_message_session_inactive(self):
        """测试会话未激活时发送消息"""
        monitor = CLIMonitor()
        monitor.session_active = False

        with pytest.raises(RuntimeError, match="CLI 会话未激活"):
            await monitor.send_message("test message")

    @pytest.mark.asyncio
    async def test_send_message_no_terminal(self):
        """测试没有终端适配器时发送消息"""
        monitor = CLIMonitor()
        monitor.session_active = True
        monitor._terminal = None

        with pytest.raises(RuntimeError, match="没有可用的终端适配器"):
            await monitor.send_message("test message")

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """测试成功发送消息"""
        mock_terminal = MagicMock()
        mock_terminal.send_text = AsyncMock(return_value=True)

        monitor = CLIMonitor(terminal_adapter=mock_terminal)
        monitor.session_active = True

        await monitor.send_message("test message", press_enter=True)

        mock_terminal.send_text.assert_called_once_with("test message", press_enter=True)


class TestCLIMonitorStatus:
    """测试状态获取"""

    @pytest.mark.asyncio
    async def test_get_status_no_adapter(self):
        """测试没有适配器时获取状态"""
        monitor = CLIMonitor()
        monitor._cli_adapter = None

        status = await monitor.get_status()

        assert isinstance(status, CLIStatus)
        assert status.is_running is False

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """测试成功获取状态"""
        mock_cli = MagicMock()
        mock_status = CLIStatus(is_running=True, context_usage=0.5)
        mock_cli.get_status = AsyncMock(return_value=mock_status)

        monitor = CLIMonitor(cli_adapter=mock_cli)

        status = await monitor.get_status()

        assert status.is_running is True
        assert status.context_usage == 0.5

    @pytest.mark.asyncio
    async def test_should_restart_session_no_adapter(self):
        """测试没有适配器时不需要重启"""
        monitor = CLIMonitor()
        monitor._cli_adapter = None

        result = await monitor.should_restart_session()
        assert result is False

    @pytest.mark.asyncio
    async def test_should_restart_session_no_status_support(self):
        """测试不支持状态检查时不需要重启"""
        mock_cli = MagicMock()
        mock_cli.supports_status_check.return_value = False

        monitor = CLIMonitor(cli_adapter=mock_cli)

        result = await monitor.should_restart_session()
        assert result is False

    @pytest.mark.asyncio
    async def test_should_restart_session_low_usage(self):
        """测试上下文使用率低时不需要重启"""
        mock_cli = MagicMock()
        mock_cli.supports_status_check.return_value = True
        mock_cli.get_status = AsyncMock(return_value=CLIStatus(is_running=True, context_usage=0.5))

        monitor = CLIMonitor(cli_adapter=mock_cli, context_threshold=0.8)

        result = await monitor.should_restart_session()
        assert result is False

    @pytest.mark.asyncio
    async def test_should_restart_session_high_usage(self):
        """测试上下文使用率高时需要重启"""
        mock_cli = MagicMock()
        mock_cli.supports_status_check.return_value = True
        mock_cli.get_status = AsyncMock(return_value=CLIStatus(is_running=True, context_usage=0.9))

        monitor = CLIMonitor(cli_adapter=mock_cli, context_threshold=0.8)

        result = await monitor.should_restart_session()
        assert result is True


class TestCLIMonitorRestart:
    """测试重启和清理"""

    @pytest.mark.asyncio
    async def test_restart_session_no_project(self):
        """测试没有项目信息时重启"""
        monitor = CLIMonitor()
        monitor.current_project_dir = None

        with pytest.raises(RuntimeError, match="没有当前任务信息"):
            await monitor.restart_session()

    @pytest.mark.asyncio
    async def test_cleanup_session(self):
        """测试清理会话"""
        mock_terminal = MagicMock()
        mock_terminal.close_window = AsyncMock()

        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"

        monitor = CLIMonitor(
            terminal_adapter=mock_terminal,
            cli_adapter=mock_cli
        )
        monitor.session_active = True
        monitor.current_task_id = "task_123"
        monitor.current_api_base_url = "http://localhost:8080"

        await monitor.cleanup_session()

        assert monitor.session_active is False
        assert monitor.current_task_id is None
        assert monitor.current_api_base_url is None
        mock_terminal.close_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_session_no_terminal(self):
        """测试没有终端时清理会话"""
        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"

        monitor = CLIMonitor(cli_adapter=mock_cli)
        monitor._terminal = None
        monitor.session_active = True

        # 不应该抛出异常
        await monitor.cleanup_session()

        assert monitor.session_active is False


class TestCLIMonitorProperties:
    """测试属性访问"""

    def test_cli_adapter_property(self):
        """测试 cli_adapter 属性"""
        mock_cli = MagicMock()
        monitor = CLIMonitor(cli_adapter=mock_cli)

        assert monitor.cli_adapter == mock_cli

    def test_cli_type_property(self):
        """测试 cli_type 属性"""
        monitor = CLIMonitor(cli_type="codex")
        assert monitor.cli_type == "codex"

    def test_template_service_lazy_load(self):
        """测试模板服务延迟加载"""
        monitor = CLIMonitor(db_path="/tmp/test.db")

        with patch('backend.services.template_service.TemplateService') as MockTemplateService:
            mock_service = MagicMock()
            MockTemplateService.return_value = mock_service

            # 第一次访问
            service1 = monitor.template_service
            assert service1 == mock_service
            MockTemplateService.assert_called_once_with("/tmp/test.db")

            # 第二次访问应该返回同一实例
            service2 = monitor.template_service
            assert service2 == mock_service
            # 仍然只调用一次
            MockTemplateService.assert_called_once()


class TestCLIMonitorBackwardCompat:
    """测试向后兼容"""

    def test_codex_monitor_alias(self):
        """测试 CodexMonitor 别名"""
        from core.cli_monitor import CodexMonitor
        assert CodexMonitor is CLIMonitor

    def test_codex_status_alias(self):
        """测试 CodexStatus 别名"""
        from core.cli_monitor import CodexStatus
        assert CodexStatus is CLIStatus
