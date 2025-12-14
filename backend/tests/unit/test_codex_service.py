"""
Codex Service Tests
测试 CLI/Codex 服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.codex_service import CodexService
from backend.models.schemas import CodexStatusModel


class TestCodexServiceInit:
    """测试 CodexService 初始化"""

    def test_init_default_values(self):
        """测试默认初始化"""
        service = CodexService()
        assert service.settings_service is None
        assert service.task_service is None
        assert service.session_manager is not None
        assert service.watchdog is None
        assert service._current_task_id is None

    def test_init_with_custom_values(self):
        """测试自定义初始化"""
        mock_settings = MagicMock()
        mock_task_service = MagicMock()

        service = CodexService(
            settings_service=mock_settings,
            task_service=mock_task_service,
            max_concurrent_sessions=5
        )

        assert service.settings_service == mock_settings
        assert service.task_service == mock_task_service


class TestCodexServiceAsync:
    """测试 CodexService 异步方法"""

    @pytest.mark.asyncio
    async def test_initialize_without_settings(self):
        """测试无设置服务时的初始化"""
        service = CodexService()
        await service.initialize()
        # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_initialize_with_settings(self):
        """测试有设置服务时的初始化"""
        mock_settings = MagicMock()
        mock_settings.get_max_concurrent_sessions = AsyncMock(return_value=5)

        service = CodexService(settings_service=mock_settings)
        await service.initialize()

        mock_settings.get_max_concurrent_sessions.assert_called_once()


class TestTerminalAdapter:
    """测试终端适配器获取"""

    @pytest.mark.asyncio
    async def test_get_terminal_adapter_auto(self):
        """测试自动选择终端适配器"""
        service = CodexService()

        with patch("core.terminal_adapters.get_default_terminal_adapter") as mock_get_default:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = True
            mock_get_default.return_value = mock_adapter

            adapter = await service.get_terminal_adapter("auto")

            assert adapter == mock_adapter
            mock_get_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_terminal_adapter_kitty(self):
        """测试获取 Kitty 适配器"""
        service = CodexService()

        with patch("core.terminal_adapters.KittyAdapter") as mock_kitty_class:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = True
            mock_kitty_class.return_value = mock_adapter

            adapter = await service.get_terminal_adapter("kitty")

            assert adapter == mock_adapter
            mock_kitty_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_terminal_adapter_iterm(self):
        """测试获取 iTerm 适配器"""
        service = CodexService()

        with patch("core.terminal_adapters.iTermAdapter") as mock_iterm_class:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = True
            mock_iterm_class.return_value = mock_adapter

            adapter = await service.get_terminal_adapter("iterm")

            assert adapter == mock_adapter
            mock_iterm_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_terminal_adapter_windows_terminal(self):
        """测试获取 Windows Terminal 适配器"""
        service = CodexService()

        with patch("core.terminal_adapters.WindowsTerminalAdapter") as mock_wt_class:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = True
            mock_wt_class.return_value = mock_adapter

            adapter = await service.get_terminal_adapter("windows_terminal")

            assert adapter == mock_adapter
            mock_wt_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_terminal_adapter_not_available(self):
        """测试终端适配器不可用"""
        service = CodexService()

        with patch("core.terminal_adapters.KittyAdapter") as mock_kitty_class:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = False
            mock_kitty_class.return_value = mock_adapter

            adapter = await service.get_terminal_adapter("kitty")

            assert adapter is None

    @pytest.mark.asyncio
    async def test_get_terminal_adapter_unknown_type(self):
        """测试未知终端类型"""
        service = CodexService()

        adapter = await service.get_terminal_adapter("unknown_terminal")

        assert adapter is None

    @pytest.mark.asyncio
    async def test_get_terminal_adapter_from_settings(self):
        """测试从设置读取终端类型"""
        mock_settings = MagicMock()
        mock_settings.get_terminal_type = AsyncMock(return_value="auto")

        service = CodexService(settings_service=mock_settings)

        with patch("core.terminal_adapters.get_default_terminal_adapter") as mock_get_default:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = True
            mock_get_default.return_value = mock_adapter

            adapter = await service.get_terminal_adapter()

            mock_settings.get_terminal_type.assert_called_once()
            assert adapter == mock_adapter


class TestSessionManagement:
    """测试会话管理"""

    @pytest.mark.asyncio
    async def test_start_session(self):
        """测试启动会话"""
        service = CodexService()
        service.session_manager.start_session = AsyncMock(return_value=True)

        result = await service.start_session(
            task_id="task_123",
            project_dir="/tmp/project",
            doc_path="/tmp/project/doc.md"
        )

        assert result is True
        assert service._current_task_id == "task_123"
        service.session_manager.start_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_failure(self):
        """测试启动会话失败"""
        service = CodexService()
        service.session_manager.start_session = AsyncMock(return_value=False)

        result = await service.start_session(
            task_id="task_123",
            project_dir="/tmp/project",
            doc_path="/tmp/project/doc.md"
        )

        assert result is False
        assert service._current_task_id is None

    @pytest.mark.asyncio
    async def test_start_session_with_watchdog(self):
        """测试启动会话时记录看门狗活动"""
        service = CodexService()
        service.session_manager.start_session = AsyncMock(return_value=True)
        service.watchdog = MagicMock()
        service.watchdog.record_activity = MagicMock()

        await service.start_session(
            task_id="task_123",
            project_dir="/tmp/project",
            doc_path="/tmp/project/doc.md"
        )

        service.watchdog.record_activity.assert_called_once_with("task_123")

    @pytest.mark.asyncio
    async def test_start_session_exception(self):
        """测试启动会话异常"""
        service = CodexService()
        service.session_manager.start_session = AsyncMock(side_effect=Exception("Error"))

        result = await service.start_session(
            task_id="task_123",
            project_dir="/tmp/project",
            doc_path="/tmp/project/doc.md"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_session(self):
        """测试停止会话"""
        service = CodexService()
        service.session_manager.stop_session = AsyncMock()
        service._current_task_id = "task_123"

        await service.stop_session("task_123")

        service.session_manager.stop_session.assert_called_once_with("task_123")
        assert service._current_task_id is None

    @pytest.mark.asyncio
    async def test_stop_session_with_watchdog(self):
        """测试停止会话时清除看门狗活动"""
        service = CodexService()
        service.session_manager.stop_session = AsyncMock()
        service.watchdog = MagicMock()
        service.watchdog.clear_activity = MagicMock()
        service._current_task_id = "task_123"

        await service.stop_session("task_123")

        service.watchdog.clear_activity.assert_called_once_with("task_123")

    @pytest.mark.asyncio
    async def test_stop_session_backward_compat(self):
        """测试停止会话向后兼容（无 task_id）"""
        service = CodexService()
        service.session_manager.stop_session = AsyncMock()
        service._current_task_id = "task_123"

        await service.stop_session()

        service.session_manager.stop_session.assert_called_once_with("task_123")

    @pytest.mark.asyncio
    async def test_stop_session_no_task(self):
        """测试无任务时停止会话"""
        service = CodexService()
        service.session_manager.stop_session = AsyncMock()

        await service.stop_session()

        # 不应该调用 stop_session
        service.session_manager.stop_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_all_sessions(self):
        """测试停止所有会话"""
        service = CodexService()
        service.session_manager.stop_all_sessions = AsyncMock()
        service._current_task_id = "task_123"

        await service.stop_all_sessions()

        service.session_manager.stop_all_sessions.assert_called_once()
        assert service._current_task_id is None


class TestGetStatus:
    """测试获取状态"""

    @pytest.mark.asyncio
    async def test_get_status_no_task(self):
        """测试无任务时获取状态"""
        service = CodexService()

        status = await service.get_status()

        assert status.is_running is False
        assert status.current_task_id is None

    @pytest.mark.asyncio
    async def test_get_status_no_session(self):
        """测试有任务但无会话时获取状态"""
        service = CodexService()
        service.session_manager.get_session = AsyncMock(return_value=None)
        service._current_task_id = "task_123"

        status = await service.get_status()

        assert status.is_running is False
        assert status.current_task_id == "task_123"

    @pytest.mark.asyncio
    async def test_get_status_with_session(self):
        """测试有会话时获取状态"""
        from core.session import SessionStatus

        service = CodexService()

        mock_session = MagicMock()
        mock_session.status = SessionStatus.RUNNING

        service.session_manager.get_session = AsyncMock(return_value=mock_session)
        service._current_task_id = "task_123"

        status = await service.get_status()

        assert status.is_running is True
        assert status.current_task_id == "task_123"


class TestWatchdog:
    """测试看门狗"""

    @pytest.mark.asyncio
    async def test_start_watchdog(self):
        """测试启动看门狗"""
        mock_settings = MagicMock()
        mock_settings.get_watchdog_heartbeat_timeout = AsyncMock(return_value=300.0)
        mock_settings.get_watchdog_check_interval = AsyncMock(return_value=30.0)

        service = CodexService(settings_service=mock_settings)

        with patch("backend.services.codex_service.SessionWatchdog") as mock_watchdog_class:
            mock_watchdog = MagicMock()
            mock_watchdog.start = AsyncMock()
            mock_watchdog_class.return_value = mock_watchdog

            await service.start_watchdog()

            mock_watchdog_class.assert_called_once()
            mock_watchdog.start.assert_called_once()
            assert service.watchdog == mock_watchdog

    @pytest.mark.asyncio
    async def test_stop_watchdog(self):
        """测试停止看门狗"""
        service = CodexService()
        service.watchdog = MagicMock()
        service.watchdog.stop = AsyncMock()

        await service.stop_watchdog()

        service.watchdog.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_watchdog_none(self):
        """测试停止不存在的看门狗"""
        service = CodexService()

        # 不应该抛出异常
        await service.stop_watchdog()


class TestSessionQueries:
    """测试会话查询"""

    def test_get_all_sessions(self):
        """测试获取所有会话"""
        service = CodexService()

        mock_session = MagicMock()
        mock_session.to_dict.return_value = {"task_id": "task_123"}

        service.session_manager.get_all_sessions = MagicMock(return_value=[mock_session])

        sessions = service.get_all_sessions()

        assert len(sessions) == 1
        assert sessions[0]["task_id"] == "task_123"

    def test_get_active_sessions(self):
        """测试获取活跃会话"""
        service = CodexService()

        mock_session = MagicMock()
        mock_session.to_dict.return_value = {"task_id": "task_123"}

        service.session_manager.get_active_sessions = MagicMock(return_value=[mock_session])

        sessions = service.get_active_sessions()

        assert len(sessions) == 1

    def test_get_session_count(self):
        """测试获取会话总数"""
        service = CodexService()
        service.session_manager.get_session_count = MagicMock(return_value=3)

        count = service.get_session_count()

        assert count == 3

    def test_get_active_count(self):
        """测试获取活跃会话数"""
        service = CodexService()
        service.session_manager.get_active_count = MagicMock(return_value=2)

        count = service.get_active_count()

        assert count == 2

    def test_get_available_slots(self):
        """测试获取可用槽位数"""
        service = CodexService()
        service.session_manager.get_available_slots = MagicMock(return_value=1)

        slots = service.get_available_slots()

        assert slots == 1


class TestSendMessage:
    """测试发送消息"""

    @pytest.mark.asyncio
    async def test_send_message(self):
        """测试发送消息"""
        service = CodexService()
        service.session_manager.send_message = AsyncMock()
        service._current_task_id = "task_123"

        await service.send_message("Hello", "task_123")

        service.session_manager.send_message.assert_called_once_with("task_123", "Hello")

    @pytest.mark.asyncio
    async def test_send_message_backward_compat(self):
        """测试发送消息向后兼容（无 task_id）"""
        service = CodexService()
        service.session_manager.send_message = AsyncMock()
        service._current_task_id = "task_123"

        await service.send_message("Hello")

        service.session_manager.send_message.assert_called_once_with("task_123", "Hello")

    @pytest.mark.asyncio
    async def test_send_message_no_task(self):
        """测试无任务时发送消息"""
        service = CodexService()
        service.session_manager.send_message = AsyncMock()

        await service.send_message("Hello")

        # 不应该调用 send_message
        service.session_manager.send_message.assert_not_called()


class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_current_task_id_property(self):
        """测试 current_task_id 属性"""
        service = CodexService()
        service._current_task_id = "task_123"

        assert service.current_task_id == "task_123"

    def test_monitor_property(self):
        """测试 monitor 属性（向后兼容）"""
        service = CodexService()
        service._current_task_id = "task_123"

        # 由于是同步属性，应该返回 None
        assert service.monitor is None

    @pytest.mark.asyncio
    async def test_update_terminal_adapter(self):
        """测试 update_terminal_adapter（向后兼容）"""
        service = CodexService()

        # 不应该抛出异常
        await service.update_terminal_adapter()

    @pytest.mark.asyncio
    async def test_update_cli_adapter(self):
        """测试 update_cli_adapter（向后兼容）"""
        service = CodexService()

        # 不应该抛出异常
        await service.update_cli_adapter()
