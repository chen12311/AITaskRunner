"""
Session Manager Tests
测试会话管理器
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from core.session.manager import SessionManager
from core.session.models import SessionStatus


class TestSessionManager:
    """测试 SessionManager"""

    def test_init_default(self):
        """测试默认初始化"""
        manager = SessionManager()
        assert manager.max_concurrent == 3
        assert manager.get_session_count() == 0

    def test_init_custom_concurrent(self):
        """测试自定义并发数"""
        manager = SessionManager(max_concurrent=5)
        assert manager.max_concurrent == 5

    def test_get_active_count_empty(self):
        """测试空时活跃计数"""
        manager = SessionManager()
        assert manager.get_active_count() == 0

    def test_get_available_slots(self):
        """测试可用槽位"""
        manager = SessionManager(max_concurrent=3)
        assert manager.get_available_slots() == 3

    def test_get_all_sessions_empty(self):
        """测试空时获取所有会话"""
        manager = SessionManager()
        assert manager.get_all_sessions() == []

    def test_get_active_sessions_empty(self):
        """测试空时获取活跃会话"""
        manager = SessionManager()
        assert manager.get_active_sessions() == []


class TestSessionManagerAsync:
    """测试 SessionManager 异步方法"""

    @pytest.mark.asyncio
    async def test_get_session_not_exists(self):
        """测试获取不存在的会话"""
        manager = SessionManager()
        session = await manager.get_session("nonexistent")
        assert session is None

    @pytest.mark.asyncio
    async def test_stop_session_not_exists(self):
        """测试停止不存在的会话"""
        manager = SessionManager()
        result = await manager.stop_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_session_not_exists(self):
        """测试移除不存在的会话"""
        manager = SessionManager()
        result = await manager.remove_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_not_exists(self):
        """测试向不存在的会话发送消息"""
        manager = SessionManager()
        result = await manager.send_message("nonexistent", "test message")
        assert result is False

    @pytest.mark.asyncio
    async def test_restart_session_not_exists(self):
        """测试重启不存在的会话"""
        manager = SessionManager()
        result = await manager.restart_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_stop_all_sessions_empty(self):
        """测试空时停止所有会话"""
        manager = SessionManager()
        await manager.stop_all_sessions()
        assert manager.get_session_count() == 0


class TestSessionManagerWithMocks:
    """使用 mock 测试 SessionManager"""

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """测试成功创建会话"""
        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.is_available.return_value = True

        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"
        mock_cli.is_available.return_value = True

        with patch.object(SessionManager, '_create_terminal_adapter', return_value=mock_terminal):
            with patch.object(SessionManager, '_create_cli_adapter', return_value=mock_cli):
                with patch.object(SessionManager, '_get_cli_type', return_value="claude_code"):
                    manager = SessionManager(max_concurrent=3)

                    session = await manager.create_session(
                        task_id="task_123",
                        project_dir="/tmp/project",
                        doc_path="/tmp/project/TODO.md"
                    )

                    assert session is not None
                    assert session.task_id == "task_123"
                    assert session.status == SessionStatus.IDLE
                    assert manager.get_session_count() == 1

    @pytest.mark.asyncio
    async def test_create_session_terminal_unavailable(self):
        """测试终端不可用时创建失败"""
        with patch.object(SessionManager, '_create_terminal_adapter', return_value=None):
            with patch.object(SessionManager, '_get_cli_type', return_value="claude_code"):
                manager = SessionManager(max_concurrent=3)

                session = await manager.create_session(
                    task_id="task_123",
                    project_dir="/tmp/project",
                    doc_path="/tmp/project/TODO.md"
                )

                assert session is None

    @pytest.mark.asyncio
    async def test_create_session_cli_unavailable(self):
        """测试 CLI 不可用时创建失败"""
        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.is_available.return_value = True

        with patch.object(SessionManager, '_create_terminal_adapter', return_value=mock_terminal):
            with patch.object(SessionManager, '_create_cli_adapter', return_value=None):
                with patch.object(SessionManager, '_get_cli_type', return_value="claude_code"):
                    manager = SessionManager(max_concurrent=3)

                    session = await manager.create_session(
                        task_id="task_123",
                        project_dir="/tmp/project",
                        doc_path="/tmp/project/TODO.md"
                    )

                    assert session is None

    @pytest.mark.asyncio
    async def test_max_concurrent_limit(self):
        """测试最大并发限制"""
        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.is_available.return_value = True

        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"
        mock_cli.is_available.return_value = True

        with patch.object(SessionManager, '_create_terminal_adapter', return_value=mock_terminal):
            with patch.object(SessionManager, '_create_cli_adapter', return_value=mock_cli):
                with patch.object(SessionManager, '_get_cli_type', return_value="claude_code"):
                    manager = SessionManager(max_concurrent=2)

                    # 创建两个会话
                    session1 = await manager.create_session(
                        task_id="task_1",
                        project_dir="/tmp/p1",
                        doc_path="/tmp/p1/TODO.md"
                    )
                    session2 = await manager.create_session(
                        task_id="task_2",
                        project_dir="/tmp/p2",
                        doc_path="/tmp/p2/TODO.md"
                    )

                    assert session1 is not None
                    assert session2 is not None
                    assert manager.get_session_count() == 2

                    # 第三个会话应该失败（达到限制）
                    session3 = await manager.create_session(
                        task_id="task_3",
                        project_dir="/tmp/p3",
                        doc_path="/tmp/p3/TODO.md"
                    )

                    assert session3 is None


class TestSessionManagerUpdateConcurrent:
    """测试更新最大并发数"""

    @pytest.mark.asyncio
    async def test_update_max_concurrent(self):
        """测试更新最大并发数"""
        manager = SessionManager(max_concurrent=3)
        await manager.update_max_concurrent(5)
        assert manager.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_update_max_concurrent_invalid(self):
        """测试无效的最大并发数"""
        manager = SessionManager(max_concurrent=3)
        await manager.update_max_concurrent(0)
        # 无效值不应该更新
        assert manager.max_concurrent == 3


class TestSessionManagerLockTimeout:
    """测试锁超时场景"""

    @pytest.mark.asyncio
    async def test_acquire_lock_timeout(self):
        """测试获取锁超时"""
        manager = SessionManager()
        # 先获取锁
        await manager._lock.acquire()

        # 尝试获取锁应该超时
        result = await manager._acquire_lock(timeout=0.1)
        assert result is False

        # 释放锁
        manager._lock.release()

    @pytest.mark.asyncio
    async def test_acquire_semaphore_timeout(self):
        """测试获取信号量超时"""
        manager = SessionManager(max_concurrent=1)
        # 先获取信号量
        await manager._semaphore.acquire()

        # 尝试获取信号量应该超时
        result = await manager._acquire_semaphore(timeout=0.1)
        assert result is False

        # 释放信号量
        manager._semaphore.release()


class TestSessionManagerTerminalTypes:
    """测试终端类型创建"""

    @pytest.mark.asyncio
    async def test_create_terminal_adapter_kitty(self):
        """测试创建 Kitty 终端适配器"""
        manager = SessionManager()

        with patch.object(manager, '_get_terminal_type', return_value="kitty"):
            with patch('core.session.manager.KittyAdapter') as mock_kitty:
                mock_instance = MagicMock()
                mock_instance.is_available.return_value = True
                mock_kitty.return_value = mock_instance

                adapter = await manager._create_terminal_adapter()
                assert adapter is mock_instance

    @pytest.mark.asyncio
    async def test_create_terminal_adapter_iterm(self):
        """测试创建 iTerm 终端适配器"""
        manager = SessionManager()

        with patch.object(manager, '_get_terminal_type', return_value="iterm"):
            with patch('core.session.manager.iTermAdapter') as mock_iterm:
                mock_instance = MagicMock()
                mock_instance.is_available.return_value = True
                mock_iterm.return_value = mock_instance

                adapter = await manager._create_terminal_adapter()
                assert adapter is mock_instance

    @pytest.mark.asyncio
    async def test_create_terminal_adapter_windows(self):
        """测试创建 Windows Terminal 适配器"""
        manager = SessionManager()

        with patch.object(manager, '_get_terminal_type', return_value="windows_terminal"):
            with patch('core.session.manager.WindowsTerminalAdapter') as mock_wt:
                mock_instance = MagicMock()
                mock_instance.is_available.return_value = True
                mock_wt.return_value = mock_instance

                adapter = await manager._create_terminal_adapter()
                assert adapter is mock_instance

    @pytest.mark.asyncio
    async def test_create_terminal_adapter_auto(self):
        """测试自动选择终端适配器"""
        manager = SessionManager()

        with patch.object(manager, '_get_terminal_type', return_value="auto"):
            with patch('core.session.manager.get_default_terminal_adapter') as mock_get:
                mock_instance = MagicMock()
                mock_instance.is_available.return_value = True
                mock_get.return_value = mock_instance

                adapter = await manager._create_terminal_adapter()
                assert adapter is mock_instance

    @pytest.mark.asyncio
    async def test_create_terminal_adapter_unsupported(self):
        """测试不支持的终端类型"""
        manager = SessionManager()

        with patch.object(manager, '_get_terminal_type', return_value="unsupported"):
            adapter = await manager._create_terminal_adapter()
            assert adapter is None

    @pytest.mark.asyncio
    async def test_create_terminal_adapter_unavailable(self):
        """测试终端适配器不可用"""
        manager = SessionManager()

        with patch.object(manager, '_get_terminal_type', return_value="kitty"):
            with patch('core.session.manager.KittyAdapter') as mock_kitty:
                mock_instance = MagicMock()
                mock_instance.is_available.return_value = False
                mock_kitty.return_value = mock_instance

                adapter = await manager._create_terminal_adapter()
                assert adapter is None


class TestSessionManagerCLIAdapter:
    """测试 CLI 适配器创建"""

    def test_create_cli_adapter_success(self):
        """测试成功创建 CLI 适配器"""
        manager = SessionManager()

        with patch('core.session.manager.get_cli_adapter') as mock_get:
            mock_adapter = MagicMock()
            mock_adapter.is_available.return_value = True
            mock_get.return_value = mock_adapter

            adapter = manager._create_cli_adapter("claude_code")
            assert adapter is mock_adapter

    def test_create_cli_adapter_unavailable(self):
        """测试 CLI 适配器不可用"""
        manager = SessionManager()

        with patch('core.session.manager.get_cli_adapter') as mock_get:
            mock_adapter = MagicMock()
            mock_adapter.name = "Claude Code"
            mock_adapter.is_available.return_value = False
            mock_get.return_value = mock_adapter

            adapter = manager._create_cli_adapter("claude_code")
            assert adapter is None

    def test_create_cli_adapter_invalid_type(self):
        """测试无效的 CLI 类型"""
        manager = SessionManager()

        with patch('core.session.manager.get_cli_adapter') as mock_get:
            mock_get.side_effect = ValueError("Invalid CLI type")

            adapter = manager._create_cli_adapter("invalid")
            assert adapter is None


class TestSessionManagerServices:
    """测试服务属性"""

    @pytest.mark.asyncio
    async def test_get_terminal_type_with_service(self):
        """测试有设置服务时获取终端类型"""
        mock_settings = AsyncMock()
        mock_settings.get_terminal_type.return_value = "kitty"

        manager = SessionManager(settings_service=mock_settings)
        result = await manager._get_terminal_type()

        assert result == "kitty"
        mock_settings.get_terminal_type.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_terminal_type_without_service(self):
        """测试无设置服务时获取终端类型"""
        manager = SessionManager()
        result = await manager._get_terminal_type()
        assert result == "auto"

    @pytest.mark.asyncio
    async def test_get_cli_type_with_service(self):
        """测试有设置服务时获取 CLI 类型"""
        mock_settings = AsyncMock()
        mock_settings.get_cli_type.return_value = "codex"

        manager = SessionManager(settings_service=mock_settings)
        result = await manager._get_cli_type()

        assert result == "codex"
        mock_settings.get_cli_type.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cli_type_without_service(self):
        """测试无设置服务时获取 CLI 类型"""
        manager = SessionManager()
        result = await manager._get_cli_type()
        assert result == "claude_code"


class TestSessionManagerStartSession:
    """测试启动会话"""

    @pytest.mark.asyncio
    async def test_start_session_missing_params(self):
        """测试缺少参数时启动失败"""
        manager = SessionManager()

        # 缺少 project_dir 和 doc_path
        result = await manager.start_session(task_id="task_123")
        assert result is False

    @pytest.mark.asyncio
    async def test_start_session_create_fails(self):
        """测试创建会话失败时启动失败"""
        manager = SessionManager()

        with patch.object(manager, 'create_session', return_value=None):
            result = await manager.start_session(
                task_id="task_123",
                project_dir="/tmp/project",
                doc_path="/tmp/project/TODO.md"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_start_session_existing_active(self):
        """测试已有活跃会话时返回成功"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.verify_alive.return_value = True
        mock_session.is_terminal.return_value = False
        mock_session.semaphore_acquired = True

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.start_session(
                task_id="task_123",
                project_dir="/tmp/project",
                doc_path="/tmp/project/TODO.md"
            )
            assert result is True


class TestSessionManagerStopSession:
    """测试停止会话"""

    @pytest.mark.asyncio
    async def test_stop_session_already_terminal(self):
        """测试停止已终止的会话"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.is_terminal.return_value = True
        mock_session.semaphore_acquired = True
        mock_session.terminal = MagicMock()
        mock_session.terminal.has_active_session.return_value = False

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.stop_session("task_123")
            assert result is True
            assert mock_session.semaphore_acquired is False

    @pytest.mark.asyncio
    async def test_stop_session_with_active_terminal(self):
        """测试停止有活跃终端的会话"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.has_active_session.return_value = True
        mock_terminal.close_window = AsyncMock()

        mock_session = MagicMock()
        mock_session.is_terminal.return_value = True
        mock_session.semaphore_acquired = True
        mock_session.terminal = mock_terminal

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.stop_session("task_123")
            assert result is True
            mock_terminal.close_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_session_running(self):
        """测试停止运行中的会话"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.close_window = AsyncMock()

        mock_session = MagicMock()
        mock_session.is_terminal.return_value = False
        mock_session.semaphore_acquired = True
        mock_session.terminal = mock_terminal
        mock_session.monitor_task = None
        mock_session.mark_stopping = MagicMock()
        mock_session.mark_stopped = MagicMock()

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.stop_session("task_123")
            assert result is True
            mock_session.mark_stopping.assert_called_once()
            mock_session.mark_stopped.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_session_with_monitor_task(self):
        """测试停止有监控任务的会话"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.close_window = AsyncMock()

        # 创建一个已完成的 mock task
        mock_task = asyncio.create_task(asyncio.sleep(10))

        mock_session = MagicMock()
        mock_session.is_terminal.return_value = False
        mock_session.semaphore_acquired = True
        mock_session.terminal = mock_terminal
        mock_session.monitor_task = mock_task
        mock_session.mark_stopping = MagicMock()
        mock_session.mark_stopped = MagicMock()

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.stop_session("task_123", timeout=0.1)
            assert result is True
            assert mock_task.cancelled()


class TestSessionManagerSendMessage:
    """测试发送消息"""

    @pytest.mark.asyncio
    async def test_send_message_session_not_active(self):
        """测试向非活跃会话发送消息"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.is_active.return_value = False

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.send_message("task_123", "test message")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """测试成功发送消息"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.send_text = AsyncMock(return_value=True)

        mock_session = MagicMock()
        mock_session.is_active.return_value = True
        mock_session.terminal = mock_terminal

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.send_message("task_123", "test message")
            assert result is True
            mock_terminal.send_text.assert_called_once_with("test message", press_enter=True)

    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """测试发送消息失败"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.send_text = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.is_active.return_value = True
        mock_session.terminal = mock_terminal

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.send_message("task_123", "test message")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_timeout(self):
        """测试发送消息超时"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.send_text = AsyncMock(side_effect=asyncio.TimeoutError())

        mock_session = MagicMock()
        mock_session.is_active.return_value = True
        mock_session.terminal = mock_terminal

        with patch.object(manager, 'get_session', return_value=mock_session):
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                result = await manager.send_message("task_123", "test message")
                assert result is False

    @pytest.mark.asyncio
    async def test_send_message_exception(self):
        """测试发送消息异常"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.send_text = AsyncMock(side_effect=Exception("Test error"))

        mock_session = MagicMock()
        mock_session.is_active.return_value = True
        mock_session.terminal = mock_terminal

        with patch.object(manager, 'get_session', return_value=mock_session):
            result = await manager.send_message("task_123", "test message")
            assert result is False


class TestSessionManagerRemoveSession:
    """测试移除会话"""

    @pytest.mark.asyncio
    async def test_remove_session_success(self):
        """测试成功移除会话"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.task_id = "task_123"
        mock_session.semaphore_acquired = True
        mock_session.terminal = None
        mock_session.monitor_task = None
        mock_session.mark_stopped = MagicMock()

        # 手动添加会话
        manager._sessions["task_123"] = mock_session

        with patch.object(manager, '_cleanup_session', new_callable=AsyncMock):
            result = await manager.remove_session("task_123")
            assert result is True
            assert "task_123" not in manager._sessions


class TestSessionManagerCleanupSession:
    """测试清理会话"""

    @pytest.mark.asyncio
    async def test_cleanup_session_with_monitor_task(self):
        """测试清理有监控任务的会话"""
        manager = SessionManager()

        # 创建一个真实的 asyncio task
        mock_task = asyncio.create_task(asyncio.sleep(10))

        mock_session = MagicMock()
        mock_session.task_id = "task_123"
        mock_session.monitor_task = mock_task
        mock_session.terminal = None
        mock_session.mark_stopped = MagicMock()

        await manager._cleanup_session(mock_session, timeout=0.1)
        assert mock_task.cancelled()
        mock_session.mark_stopped.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_session_with_terminal(self):
        """测试清理有终端的会话"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.has_active_session.return_value = True
        mock_terminal.close_window = AsyncMock()

        mock_session = MagicMock()
        mock_session.task_id = "task_123"
        mock_session.monitor_task = None
        mock_session.terminal = mock_terminal
        mock_session.mark_stopped = MagicMock()

        await manager._cleanup_session(mock_session)
        mock_terminal.close_window.assert_called_once()
        mock_session.mark_stopped.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_session_terminal_timeout(self):
        """测试清理会话时终端关闭超时"""
        manager = SessionManager()

        mock_terminal = AsyncMock()
        mock_terminal.has_active_session.return_value = True

        mock_session = MagicMock()
        mock_session.task_id = "task_123"
        mock_session.monitor_task = None
        mock_session.terminal = mock_terminal
        mock_session.mark_stopped = MagicMock()

        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            await manager._cleanup_session(mock_session)
            mock_session.mark_stopped.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_session_exception(self):
        """测试清理会话时发生异常"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.task_id = "task_123"
        mock_session.monitor_task = None
        mock_session.terminal = MagicMock()
        mock_session.terminal.has_active_session.side_effect = Exception("Test error")

        # 不应该抛出异常
        await manager._cleanup_session(mock_session)


class TestSessionManagerRestartSession:
    """测试重启会话"""

    @pytest.mark.asyncio
    async def test_restart_session_success(self):
        """测试成功重启会话"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.api_base_url = "http://127.0.0.1:8086"

        mock_template_service = AsyncMock()
        mock_template_service.render_template_async = AsyncMock(return_value="Resume message")
        manager._template_service = mock_template_service

        with patch.object(manager, 'get_session', return_value=mock_session):
            with patch.object(manager, 'stop_session', new_callable=AsyncMock):
                with patch.object(manager, 'start_session', new_callable=AsyncMock, return_value=True):
                    with patch.object(manager, 'send_message', new_callable=AsyncMock, return_value=True):
                        result = await manager.restart_session("task_123")
                        assert result is True

    @pytest.mark.asyncio
    async def test_restart_session_start_fails(self):
        """测试重启会话时启动失败"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.api_base_url = "http://127.0.0.1:8086"

        with patch.object(manager, 'get_session', return_value=mock_session):
            with patch.object(manager, 'stop_session', new_callable=AsyncMock):
                with patch.object(manager, 'start_session', new_callable=AsyncMock, return_value=False):
                    result = await manager.restart_session("task_123")
                    assert result is False


class TestSessionManagerStopAllSessions:
    """测试停止所有会话"""

    @pytest.mark.asyncio
    async def test_stop_all_sessions_with_sessions(self):
        """测试停止多个会话"""
        manager = SessionManager()

        mock_session1 = MagicMock()
        mock_session1.task_id = "task_1"
        mock_session2 = MagicMock()
        mock_session2.task_id = "task_2"

        manager._sessions = {"task_1": mock_session1, "task_2": mock_session2}

        with patch.object(manager, 'stop_session', new_callable=AsyncMock, return_value=True):
            await manager.stop_all_sessions()
            # 验证 stop_session 被调用了两次
            assert manager.stop_session.call_count == 2


class TestSessionManagerCreateSessionEdgeCases:
    """测试创建会话的边界情况"""

    @pytest.mark.asyncio
    async def test_create_session_existing_active(self):
        """测试创建已存在的活跃会话"""
        manager = SessionManager()

        mock_session = MagicMock()
        mock_session.is_active.return_value = True
        mock_session.semaphore_acquired = True

        manager._sessions["task_123"] = mock_session

        result = await manager.create_session(
            task_id="task_123",
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert result is mock_session

    @pytest.mark.asyncio
    async def test_create_session_existing_inactive(self):
        """测试创建已存在但不活跃的会话"""
        manager = SessionManager()

        mock_old_session = MagicMock()
        mock_old_session.is_active.return_value = False
        mock_old_session.semaphore_acquired = True
        mock_old_session.terminal = None
        mock_old_session.monitor_task = None
        mock_old_session.mark_stopped = MagicMock()

        manager._sessions["task_123"] = mock_old_session

        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.is_available.return_value = True

        mock_cli = MagicMock()
        mock_cli.name = "MockCLI"
        mock_cli.is_available.return_value = True

        with patch.object(manager, '_create_terminal_adapter', return_value=mock_terminal):
            with patch.object(manager, '_create_cli_adapter', return_value=mock_cli):
                with patch.object(manager, '_get_cli_type', return_value="claude_code"):
                    with patch.object(manager, '_cleanup_session', new_callable=AsyncMock):
                        result = await manager.create_session(
                            task_id="task_123",
                            project_dir="/tmp/project",
                            doc_path="/tmp/project/TODO.md"
                        )

                        assert result is not None
                        assert result.task_id == "task_123"

    @pytest.mark.asyncio
    async def test_create_session_exception(self):
        """测试创建会话时发生异常"""
        manager = SessionManager()

        mock_terminal = MagicMock()
        mock_terminal.name = "MockTerminal"
        mock_terminal.is_available.return_value = True

        with patch.object(manager, '_create_terminal_adapter', return_value=mock_terminal):
            with patch.object(manager, '_create_cli_adapter', side_effect=Exception("Test error")):
                with patch.object(manager, '_get_cli_type', return_value="claude_code"):
                    result = await manager.create_session(
                        task_id="task_123",
                        project_dir="/tmp/project",
                        doc_path="/tmp/project/TODO.md"
                    )

                    assert result is None
