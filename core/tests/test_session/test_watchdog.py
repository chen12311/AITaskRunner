"""
Session Watchdog Tests
测试会话看门狗
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio

from core.session.watchdog import SessionWatchdog


class TestSessionWatchdogInit:
    """测试 SessionWatchdog 初始化"""

    def test_init_default(self):
        """测试默认初始化"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        assert watchdog._session_manager == mock_manager
        assert watchdog._task_service is None
        assert watchdog._heartbeat_timeout == 300.0
        assert watchdog._check_interval == 30.0
        assert watchdog._on_timeout is None
        assert watchdog._running is False
        assert watchdog._watchdog_task is None

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        mock_manager = MagicMock()
        mock_task_service = MagicMock()
        mock_callback = AsyncMock()

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            task_service=mock_task_service,
            heartbeat_timeout=600.0,
            check_interval=60.0,
            on_timeout=mock_callback
        )

        assert watchdog._task_service == mock_task_service
        assert watchdog._heartbeat_timeout == 600.0
        assert watchdog._check_interval == 60.0
        assert watchdog._on_timeout == mock_callback


class TestSessionWatchdogActivity:
    """测试活动记录"""

    def test_record_activity(self):
        """测试记录活动"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        task_id = "task_123"
        before = datetime.now()
        watchdog.record_activity(task_id)
        after = datetime.now()

        assert task_id in watchdog._last_activity
        assert before <= watchdog._last_activity[task_id] <= after

    def test_record_activity_update(self):
        """测试更新活动记录"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        task_id = "task_123"
        watchdog.record_activity(task_id)
        first_time = watchdog._last_activity[task_id]

        # 等待一小段时间后再次记录
        import time
        time.sleep(0.01)
        watchdog.record_activity(task_id)
        second_time = watchdog._last_activity[task_id]

        assert second_time > first_time

    def test_clear_activity(self):
        """测试清除活动记录"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        task_id = "task_123"
        watchdog.record_activity(task_id)
        assert task_id in watchdog._last_activity

        watchdog.clear_activity(task_id)
        assert task_id not in watchdog._last_activity

    def test_clear_activity_nonexistent(self):
        """测试清除不存在的活动记录"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        # 不应该抛出异常
        watchdog.clear_activity("nonexistent_task")


class TestSessionWatchdogStartStop:
    """测试启动和停止"""

    @pytest.mark.asyncio
    async def test_start(self):
        """测试启动看门狗"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            check_interval=0.1
        )

        await watchdog.start()

        assert watchdog._running is True
        assert watchdog._watchdog_task is not None

        # 清理
        await watchdog.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """测试已运行时再次启动"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            check_interval=0.1
        )

        await watchdog.start()
        first_task = watchdog._watchdog_task

        await watchdog.start()  # 再次启动
        second_task = watchdog._watchdog_task

        # 应该是同一个任务
        assert first_task == second_task

        # 清理
        await watchdog.stop()

    @pytest.mark.asyncio
    async def test_stop(self):
        """测试停止看门狗"""
        mock_manager = MagicMock()
        mock_manager.get_active_sessions.return_value = []

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            check_interval=0.1
        )

        await watchdog.start()
        assert watchdog._running is True

        await watchdog.stop()

        assert watchdog._running is False
        assert watchdog._watchdog_task is None

    @pytest.mark.asyncio
    async def test_stop_not_running(self):
        """测试未运行时停止"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        # 不应该抛出异常
        await watchdog.stop()
        assert watchdog._running is False


class TestSessionWatchdogHealthCheck:
    """测试健康检查"""

    def test_check_session_health_healthy(self):
        """测试健康会话"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        mock_session = MagicMock()
        mock_session.verify_alive.return_value = True

        task_id = "task_123"
        watchdog.record_activity(task_id)

        health = watchdog._check_session_health(task_id, mock_session)
        assert health == "healthy"

    def test_check_session_health_terminated(self):
        """测试已终止的会话"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        mock_session = MagicMock()
        mock_session.verify_alive.return_value = False

        health = watchdog._check_session_health("task_123", mock_session)
        assert health == "terminated"

    def test_check_session_health_idle(self):
        """测试超时空闲的会话"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            heartbeat_timeout=1.0  # 1秒超时
        )

        mock_session = MagicMock()
        mock_session.verify_alive.return_value = True

        task_id = "task_123"
        # 设置过期的活动时间
        watchdog._last_activity[task_id] = datetime.now() - timedelta(seconds=10)

        health = watchdog._check_session_health(task_id, mock_session)
        assert health == "idle"

    def test_check_session_health_no_activity_record(self):
        """测试没有活动记录的会话"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        mock_session = MagicMock()
        mock_session.verify_alive.return_value = True

        # 没有记录活动
        health = watchdog._check_session_health("task_123", mock_session)
        assert health == "healthy"  # 没有活动记录时视为健康


class TestSessionWatchdogTemplateSelection:
    """测试模板选择"""

    @pytest.mark.asyncio
    async def test_get_template_no_task_service(self):
        """测试没有任务服务时的模板选择"""
        mock_manager = MagicMock()
        watchdog = SessionWatchdog(session_manager=mock_manager)

        template = await watchdog._get_template_by_task_status("task_123")
        assert template == "continue_task"

    @pytest.mark.asyncio
    async def test_get_template_task_not_found(self):
        """测试任务不存在时的模板选择"""
        mock_manager = MagicMock()
        mock_task_service = MagicMock()
        mock_task_service.get_task_raw = AsyncMock(return_value=None)

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            task_service=mock_task_service
        )

        template = await watchdog._get_template_by_task_status("task_123")
        assert template == "continue_task"

    @pytest.mark.asyncio
    async def test_get_template_in_progress(self):
        """测试进行中任务的模板选择"""
        mock_manager = MagicMock()
        mock_task_service = MagicMock()
        mock_task_service.get_task_raw = AsyncMock(return_value={'status': 'in_progress'})

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            task_service=mock_task_service
        )

        template = await watchdog._get_template_by_task_status("task_123")
        assert template == "resume_task"

    @pytest.mark.asyncio
    async def test_get_template_in_reviewing(self):
        """测试审核中任务的模板选择"""
        mock_manager = MagicMock()
        mock_task_service = MagicMock()
        mock_task_service.get_task_raw = AsyncMock(return_value={'status': 'in_reviewing'})

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            task_service=mock_task_service
        )

        template = await watchdog._get_template_by_task_status("task_123")
        assert template == "review"

    @pytest.mark.asyncio
    async def test_get_template_other_status(self):
        """测试其他状态任务的模板选择"""
        mock_manager = MagicMock()
        mock_task_service = MagicMock()
        mock_task_service.get_task_raw = AsyncMock(return_value={'status': 'pending'})

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            task_service=mock_task_service
        )

        template = await watchdog._get_template_by_task_status("task_123")
        assert template == "continue_task"

    @pytest.mark.asyncio
    async def test_get_template_exception(self):
        """测试查询异常时的模板选择"""
        mock_manager = MagicMock()
        mock_task_service = MagicMock()
        mock_task_service.get_task_raw = AsyncMock(side_effect=Exception("DB error"))

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            task_service=mock_task_service
        )

        template = await watchdog._get_template_by_task_status("task_123")
        assert template == "continue_task"


class TestSessionWatchdogHandleTerminated:
    """测试终止处理"""

    @pytest.mark.asyncio
    async def test_handle_terminated_with_callback(self):
        """测试带回调的终止处理"""
        mock_manager = MagicMock()
        mock_manager.start_session = AsyncMock(return_value=True)
        mock_callback = AsyncMock()

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            on_timeout=mock_callback
        )

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.cli_type = "claude_code"
        mock_session.api_base_url = "http://localhost:8080"

        await watchdog._handle_terminated("task_123", mock_session)

        # 验证回调被调用
        mock_callback.assert_called_once_with("task_123", "terminated")

    @pytest.mark.asyncio
    async def test_handle_terminated_callback_error(self):
        """测试回调异常时的处理"""
        mock_manager = MagicMock()
        mock_manager.start_session = AsyncMock(return_value=True)
        mock_callback = AsyncMock(side_effect=Exception("Callback error"))

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            on_timeout=mock_callback
        )

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.cli_type = "claude_code"
        mock_session.api_base_url = "http://localhost:8080"

        # 不应该抛出异常
        await watchdog._handle_terminated("task_123", mock_session)


class TestSessionWatchdogAutoRestart:
    """测试自动重启"""

    @pytest.mark.asyncio
    async def test_auto_restart_success(self):
        """测试成功自动重启"""
        mock_manager = MagicMock()
        mock_manager.start_session = AsyncMock(return_value=True)

        watchdog = SessionWatchdog(session_manager=mock_manager)

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.cli_type = "claude_code"
        mock_session.api_base_url = "http://localhost:8080"

        task_id = "task_123"
        await watchdog._auto_restart(task_id, mock_session)

        # 验证 start_session 被调用
        mock_manager.start_session.assert_called_once()

        # 验证活动被记录
        assert task_id in watchdog._last_activity

    @pytest.mark.asyncio
    async def test_auto_restart_failure(self):
        """测试自动重启失败"""
        mock_manager = MagicMock()
        mock_manager.start_session = AsyncMock(return_value=False)

        watchdog = SessionWatchdog(session_manager=mock_manager)

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.cli_type = "claude_code"
        mock_session.api_base_url = "http://localhost:8080"

        task_id = "task_123"
        await watchdog._auto_restart(task_id, mock_session)

        # 重启失败时不应该记录活动
        assert task_id not in watchdog._last_activity

    @pytest.mark.asyncio
    async def test_auto_restart_exception(self):
        """测试自动重启异常"""
        mock_manager = MagicMock()
        mock_manager.start_session = AsyncMock(side_effect=Exception("Start error"))

        watchdog = SessionWatchdog(session_manager=mock_manager)

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.cli_type = "claude_code"
        mock_session.api_base_url = "http://localhost:8080"

        # 不应该抛出异常
        await watchdog._auto_restart("task_123", mock_session)

    @pytest.mark.asyncio
    async def test_auto_restart_with_template_selection(self):
        """测试带模板选择的自动重启"""
        mock_manager = MagicMock()
        mock_manager.start_session = AsyncMock(return_value=True)

        mock_task_service = MagicMock()
        mock_task_service.get_task_raw = AsyncMock(return_value={'status': 'in_progress'})

        watchdog = SessionWatchdog(
            session_manager=mock_manager,
            task_service=mock_task_service
        )

        mock_session = MagicMock()
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.cli_type = "claude_code"
        mock_session.api_base_url = "http://localhost:8080"

        await watchdog._auto_restart("task_123", mock_session)

        # 验证使用正确的模板
        call_args = mock_manager.start_session.call_args
        assert call_args.kwargs['template_name'] == 'resume_task'


class TestSessionWatchdogCheckAllSessions:
    """测试检查所有会话"""

    @pytest.mark.asyncio
    async def test_check_all_sessions_empty(self):
        """测试空会话列表"""
        mock_manager = MagicMock()
        mock_manager.get_active_sessions.return_value = []

        watchdog = SessionWatchdog(session_manager=mock_manager)

        # 不应该抛出异常
        await watchdog._check_all_sessions()

    @pytest.mark.asyncio
    async def test_check_all_sessions_healthy(self):
        """测试所有会话健康"""
        mock_manager = MagicMock()

        mock_session = MagicMock()
        mock_session.task_id = "task_123"
        mock_session.verify_alive.return_value = True

        mock_manager.get_active_sessions.return_value = [mock_session]

        watchdog = SessionWatchdog(session_manager=mock_manager)
        watchdog.record_activity("task_123")

        await watchdog._check_all_sessions()

        # 健康会话不应该触发重启
        assert not mock_manager.start_session.called

    @pytest.mark.asyncio
    async def test_check_all_sessions_terminated(self):
        """测试有终止会话"""
        mock_manager = MagicMock()
        mock_manager.start_session = AsyncMock(return_value=True)

        mock_session = MagicMock()
        mock_session.task_id = "task_123"
        mock_session.verify_alive.return_value = False
        mock_session.project_dir = "/tmp/project"
        mock_session.doc_path = "/tmp/project/TODO.md"
        mock_session.cli_type = "claude_code"
        mock_session.api_base_url = "http://localhost:8080"

        mock_manager.get_active_sessions.return_value = [mock_session]

        watchdog = SessionWatchdog(session_manager=mock_manager)

        await watchdog._check_all_sessions()

        # 终止会话应该触发重启
        mock_manager.start_session.assert_called_once()
