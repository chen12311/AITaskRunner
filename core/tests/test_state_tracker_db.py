"""
State Tracker DB Tests
测试基于 SQLite 的状态追踪器
"""
import pytest
import tempfile
import os
from pathlib import Path

from core.state_tracker_db import (
    TaskStatus,
    SessionStatus,
    TaskStateDAO,
    SessionStateDAO,
    StateTrackerDB,
)


class TestTaskStatus:
    """测试 TaskStatus 枚举"""

    def test_task_status_values(self):
        """测试任务状态值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.PAUSED.value == "paused"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestSessionStatus:
    """测试 SessionStatus 枚举"""

    def test_session_status_values(self):
        """测试会话状态值"""
        assert SessionStatus.IDLE.value == "idle"
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.RESTARTING.value == "restarting"
        assert SessionStatus.ERROR.value == "error"


class TestTaskStateDAO:
    """测试 TaskStateDAO"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)

    def test_init_creates_table(self, temp_db):
        """测试初始化创建表"""
        dao = TaskStateDAO(temp_db)
        assert dao._initialized is True

    def test_update_task_state_new(self, temp_db):
        """测试创建新任务状态"""
        dao = TaskStateDAO(temp_db)
        dao.update_task_state("task_1", {"status": "in_progress"})

        state = dao.get_task_state("task_1")
        assert state is not None
        assert state["task_id"] == "task_1"
        assert state["status"] == "in_progress"

    def test_update_task_state_existing(self, temp_db):
        """测试更新已存在的任务状态"""
        dao = TaskStateDAO(temp_db)
        dao.update_task_state("task_1", {"status": "pending"})
        dao.update_task_state("task_1", {"status": "in_progress", "progress": 0.5})

        state = dao.get_task_state("task_1")
        assert state["status"] == "in_progress"
        assert state["progress"] == 0.5

    def test_get_task_state_not_exists(self, temp_db):
        """测试获取不存在的任务状态"""
        dao = TaskStateDAO(temp_db)
        state = dao.get_task_state("nonexistent")
        assert state is None

    def test_get_all_states_empty(self, temp_db):
        """测试获取空状态列表"""
        dao = TaskStateDAO(temp_db)
        states = dao.get_all_states()
        assert states == []

    def test_get_all_states_multiple(self, temp_db):
        """测试获取多个状态"""
        dao = TaskStateDAO(temp_db)
        dao.update_task_state("task_1", {"status": "pending"})
        dao.update_task_state("task_2", {"status": "in_progress"})
        dao.update_task_state("task_3", {"status": "completed"})

        states = dao.get_all_states()
        assert len(states) == 3

    def test_update_with_all_fields(self, temp_db):
        """测试更新所有字段"""
        dao = TaskStateDAO(temp_db)
        dao.update_task_state("task_1", {
            "status": "in_progress",
            "progress": 0.75,
            "started_at": "2025-01-01T00:00:00",
            "error_message": None,
            "restart_count": 2
        })

        state = dao.get_task_state("task_1")
        assert state["progress"] == 0.75
        assert state["started_at"] == "2025-01-01T00:00:00"
        assert state["restart_count"] == 2


class TestSessionStateDAO:
    """测试 SessionStateDAO"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)

    def test_init_creates_table(self, temp_db):
        """测试初始化创建表"""
        dao = SessionStateDAO(temp_db)
        assert dao._initialized is True

    def test_update_session_new(self, temp_db):
        """测试创建新会话状态"""
        dao = SessionStateDAO(temp_db)
        dao.update_session("session_1", {"status": "active"})

        state = dao.get_session("session_1")
        assert state is not None
        assert state["session_id"] == "session_1"
        assert state["status"] == "active"

    def test_update_session_existing(self, temp_db):
        """测试更新已存在的会话状态"""
        dao = SessionStateDAO(temp_db)
        dao.update_session("session_1", {"status": "idle"})
        dao.update_session("session_1", {"status": "active", "current_task": "task_1"})

        state = dao.get_session("session_1")
        assert state["status"] == "active"
        assert state["current_task"] == "task_1"

    def test_get_session_not_exists(self, temp_db):
        """测试获取不存在的会话状态"""
        dao = SessionStateDAO(temp_db)
        state = dao.get_session("nonexistent")
        assert state is None

    def test_update_session_with_context_usage(self, temp_db):
        """测试更新带上下文使用信息的会话"""
        dao = SessionStateDAO(temp_db)
        context_usage = {"used": 1000, "max": 10000}
        dao.update_session("session_1", {
            "status": "active",
            "context_usage": context_usage
        })

        state = dao.get_session("session_1")
        assert state["context_usage"] == context_usage

    def test_get_session_with_invalid_json(self, temp_db):
        """测试获取带无效 JSON 的会话"""
        dao = SessionStateDAO(temp_db)
        # 先创建一个正常的会话
        dao.update_session("session_1", {"status": "active"})

        # 手动插入无效的 JSON
        import sqlite3
        conn = sqlite3.connect(temp_db)
        conn.execute(
            "UPDATE session_states SET context_usage = ? WHERE session_id = ?",
            ("invalid json", "session_1")
        )
        conn.commit()
        conn.close()

        state = dao.get_session("session_1")
        assert state["context_usage"] is None


class TestStateTrackerDB:
    """测试 StateTrackerDB"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)

    def test_init(self, temp_db):
        """测试初始化"""
        tracker = StateTrackerDB(temp_db)
        assert tracker.task_state_dao is not None
        assert tracker.session_state_dao is not None

    def test_update_task_status_pending(self, temp_db):
        """测试更新任务状态为 pending"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.PENDING)

        state = tracker.get_task_status("task_1")
        assert state["status"] == "pending"

    def test_update_task_status_in_progress(self, temp_db):
        """测试更新任务状态为 in_progress"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.IN_PROGRESS)

        state = tracker.get_task_status("task_1")
        assert state["status"] == "in_progress"
        assert state["started_at"] is not None

    def test_update_task_status_completed(self, temp_db):
        """测试更新任务状态为 completed"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.COMPLETED)

        state = tracker.get_task_status("task_1")
        assert state["status"] == "completed"
        assert state["completed_at"] is not None
        assert state["progress"] == 1.0

    def test_update_task_status_with_progress(self, temp_db):
        """测试更新任务状态带进度"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.IN_PROGRESS, progress=0.5)

        state = tracker.get_task_status("task_1")
        assert state["progress"] == 0.5

    def test_update_task_status_with_error(self, temp_db):
        """测试更新任务状态带错误信息"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status(
            "task_1",
            TaskStatus.FAILED,
            error_message="Something went wrong"
        )

        state = tracker.get_task_status("task_1")
        assert state["status"] == "failed"
        assert state["error_message"] == "Something went wrong"

    def test_get_task_status_not_exists(self, temp_db):
        """测试获取不存在的任务状态"""
        tracker = StateTrackerDB(temp_db)
        state = tracker.get_task_status("nonexistent")
        assert state is None

    def test_increment_restart_count(self, temp_db):
        """测试增加重启计数"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.PENDING)
        tracker.increment_restart_count("task_1")

        state = tracker.get_task_status("task_1")
        assert state["restart_count"] == 1

        tracker.increment_restart_count("task_1")
        state = tracker.get_task_status("task_1")
        assert state["restart_count"] == 2

    def test_increment_restart_count_nonexistent(self, temp_db):
        """测试增加不存在任务的重启计数"""
        tracker = StateTrackerDB(temp_db)
        # 不应该抛出异常
        tracker.increment_restart_count("nonexistent")

    def test_update_session_status(self, temp_db):
        """测试更新会话状态"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_session_status("session_1", SessionStatus.ACTIVE)

        state = tracker.get_session_status("session_1")
        assert state["status"] == "active"

    def test_update_session_status_with_task(self, temp_db):
        """测试更新会话状态带当前任务"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_session_status(
            "session_1",
            SessionStatus.ACTIVE,
            current_task="task_1"
        )

        state = tracker.get_session_status("session_1")
        assert state["current_task"] == "task_1"

    def test_update_session_status_with_context(self, temp_db):
        """测试更新会话状态带上下文使用"""
        tracker = StateTrackerDB(temp_db)
        context = {"used": 5000, "max": 10000}
        tracker.update_session_status(
            "session_1",
            SessionStatus.ACTIVE,
            context_usage=context
        )

        state = tracker.get_session_status("session_1")
        assert state["context_usage"] == context

    def test_get_session_status_not_exists(self, temp_db):
        """测试获取不存在的会话状态"""
        tracker = StateTrackerDB(temp_db)
        state = tracker.get_session_status("nonexistent")
        assert state is None

    def test_get_all_task_states(self, temp_db):
        """测试获取所有任务状态"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.PENDING)
        tracker.update_task_status("task_2", TaskStatus.IN_PROGRESS)

        states = tracker.get_all_task_states()
        assert len(states) == 2

    def test_get_pending_tasks(self, temp_db):
        """测试获取待处理任务"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.PENDING)
        tracker.update_task_status("task_2", TaskStatus.IN_PROGRESS)
        tracker.update_task_status("task_3", TaskStatus.PENDING)

        pending = tracker.get_pending_tasks()
        assert len(pending) == 2
        for task in pending:
            assert task["status"] == "pending"

    def test_get_in_progress_tasks(self, temp_db):
        """测试获取进行中任务"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.PENDING)
        tracker.update_task_status("task_2", TaskStatus.IN_PROGRESS)
        tracker.update_task_status("task_3", TaskStatus.IN_PROGRESS)

        in_progress = tracker.get_in_progress_tasks()
        assert len(in_progress) == 2
        for task in in_progress:
            assert task["status"] == "in_progress"

    def test_export_report_empty(self, temp_db):
        """测试导出空报告"""
        tracker = StateTrackerDB(temp_db)
        report = tracker.export_report()

        assert report["total_tasks"] == 0
        assert report["average_progress"] == 0.0
        assert report["average_restarts"] == 0.0
        assert report["tasks"] == []

    def test_export_report_with_tasks(self, temp_db):
        """测试导出带任务的报告"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.PENDING)
        tracker.update_task_status("task_2", TaskStatus.IN_PROGRESS, progress=0.5)
        tracker.update_task_status("task_3", TaskStatus.COMPLETED)

        report = tracker.export_report()

        assert report["total_tasks"] == 3
        assert report["status_counts"]["pending"] == 1
        assert report["status_counts"]["in_progress"] == 1
        assert report["status_counts"]["completed"] == 1
        assert "timestamp" in report
        assert len(report["tasks"]) == 3

    def test_export_report_average_progress(self, temp_db):
        """测试导出报告的平均进度"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.IN_PROGRESS, progress=0.0)
        tracker.update_task_status("task_2", TaskStatus.IN_PROGRESS, progress=0.5)
        tracker.update_task_status("task_3", TaskStatus.COMPLETED)  # progress = 1.0

        report = tracker.export_report()
        # (0.0 + 0.5 + 1.0) / 3 = 0.5
        assert report["average_progress"] == 0.5

    def test_export_report_average_restarts(self, temp_db):
        """测试导出报告的平均重启次数"""
        tracker = StateTrackerDB(temp_db)
        tracker.update_task_status("task_1", TaskStatus.PENDING)
        tracker.increment_restart_count("task_1")
        tracker.increment_restart_count("task_1")

        tracker.update_task_status("task_2", TaskStatus.PENDING)
        tracker.increment_restart_count("task_2")

        report = tracker.export_report()
        # (2 + 1) / 2 = 1.5
        assert report["average_restarts"] == 1.5
