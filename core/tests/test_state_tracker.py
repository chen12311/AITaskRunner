"""
State Tracker Tests
测试状态追踪器
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

from core.state_tracker import (
    StateTracker,
    TaskState,
    SessionState,
    TaskStatus,
    SessionStatus
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


class TestTaskState:
    """测试 TaskState"""

    def test_create_task_state(self):
        """测试创建任务状态"""
        state = TaskState(
            task_file="/tmp/task.md",
            status=TaskStatus.PENDING,
            progress=0.0
        )

        assert state.task_file == "/tmp/task.md"
        assert state.status == TaskStatus.PENDING
        assert state.progress == 0.0
        assert state.restart_count == 0

    def test_to_dict(self):
        """测试转换为字典"""
        state = TaskState(
            task_file="/tmp/task.md",
            status=TaskStatus.IN_PROGRESS,
            progress=0.5,
            started_at="2024-01-01T10:00:00",
            error_message="test error"
        )

        data = state.to_dict()

        assert data["task_file"] == "/tmp/task.md"
        assert data["status"] == "in_progress"
        assert data["progress"] == 0.5
        assert data["started_at"] == "2024-01-01T10:00:00"
        assert data["error_message"] == "test error"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "task_file": "/tmp/task.md",
            "status": "completed",
            "progress": 1.0,
            "started_at": "2024-01-01T10:00:00",
            "completed_at": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
            "error_message": None,
            "restart_count": 2
        }

        state = TaskState.from_dict(data)

        assert state.task_file == "/tmp/task.md"
        assert state.status == TaskStatus.COMPLETED
        assert state.progress == 1.0
        assert state.restart_count == 2


class TestSessionState:
    """测试 SessionState"""

    def test_create_session_state(self):
        """测试创建会话状态"""
        state = SessionState(
            session_id="session_123",
            status=SessionStatus.ACTIVE,
            current_task="/tmp/task.md",
            context_usage=0.5,
            started_at="2024-01-01T10:00:00",
            last_activity="2024-01-01T10:30:00"
        )

        assert state.session_id == "session_123"
        assert state.status == SessionStatus.ACTIVE
        assert state.current_task == "/tmp/task.md"
        assert state.context_usage == 0.5

    def test_to_dict(self):
        """测试转换为字典"""
        state = SessionState(
            session_id="session_123",
            status=SessionStatus.ACTIVE,
            current_task="/tmp/task.md",
            context_usage=0.5,
            started_at="2024-01-01T10:00:00",
            last_activity="2024-01-01T10:30:00"
        )

        data = state.to_dict()

        assert data["session_id"] == "session_123"
        assert data["status"] == "active"
        assert data["context_usage"] == 0.5

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "session_id": "session_123",
            "status": "idle",
            "current_task": None,
            "context_usage": 0.0,
            "started_at": "2024-01-01T10:00:00",
            "last_activity": "2024-01-01T10:00:00"
        }

        state = SessionState.from_dict(data)

        assert state.session_id == "session_123"
        assert state.status == SessionStatus.IDLE
        assert state.current_task is None


class TestStateTracker:
    """测试 StateTracker"""

    @pytest.fixture
    def temp_state_file(self):
        """创建临时状态文件"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            yield f.name
        # 清理
        if os.path.exists(f.name):
            os.remove(f.name)

    def test_init_new_file(self, temp_state_file):
        """测试初始化（新文件）"""
        tracker = StateTracker(state_file=temp_state_file)

        assert tracker.tasks == {}
        assert tracker.session is None

    def test_init_existing_file(self, temp_state_file):
        """测试初始化（已有文件）"""
        # 预先创建状态文件
        initial_data = {
            "tasks": {
                "/tmp/task.md": {
                    "task_file": "/tmp/task.md",
                    "status": "pending",
                    "progress": 0.0,
                    "started_at": None,
                    "completed_at": None,
                    "last_updated": "2024-01-01T10:00:00",
                    "error_message": None,
                    "restart_count": 0
                }
            },
            "session": None
        }

        with open(temp_state_file, 'w') as f:
            json.dump(initial_data, f)

        tracker = StateTracker(state_file=temp_state_file)

        assert "/tmp/task.md" in tracker.tasks
        assert tracker.tasks["/tmp/task.md"].status == TaskStatus.PENDING

    def test_update_task_status_new_task(self, temp_state_file):
        """测试更新新任务状态"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status(
            task_file="/tmp/task.md",
            status=TaskStatus.PENDING,
            progress=0.0
        )

        assert "/tmp/task.md" in tracker.tasks
        assert tracker.tasks["/tmp/task.md"].status == TaskStatus.PENDING
        assert tracker.tasks["/tmp/task.md"].progress == 0.0

    def test_update_task_status_existing_task(self, temp_state_file):
        """测试更新已有任务状态"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status(
            task_file="/tmp/task.md",
            status=TaskStatus.PENDING,
            progress=0.0
        )

        tracker.update_task_status(
            task_file="/tmp/task.md",
            status=TaskStatus.IN_PROGRESS,
            progress=0.5
        )

        assert tracker.tasks["/tmp/task.md"].status == TaskStatus.IN_PROGRESS
        assert tracker.tasks["/tmp/task.md"].progress == 0.5
        assert tracker.tasks["/tmp/task.md"].started_at is not None

    def test_update_task_status_completed(self, temp_state_file):
        """测试更新任务为完成状态"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status(
            task_file="/tmp/task.md",
            status=TaskStatus.COMPLETED,
            progress=1.0
        )

        assert tracker.tasks["/tmp/task.md"].status == TaskStatus.COMPLETED
        assert tracker.tasks["/tmp/task.md"].completed_at is not None

    def test_update_task_status_with_error(self, temp_state_file):
        """测试更新任务状态带错误信息"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status(
            task_file="/tmp/task.md",
            status=TaskStatus.FAILED,
            progress=0.5,
            error_message="Something went wrong"
        )

        assert tracker.tasks["/tmp/task.md"].status == TaskStatus.FAILED
        assert tracker.tasks["/tmp/task.md"].error_message == "Something went wrong"

    def test_update_session_status_new(self, temp_state_file):
        """测试更新新会话状态"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_session_status(
            session_id="session_123",
            status=SessionStatus.ACTIVE,
            current_task="/tmp/task.md",
            context_usage=0.3
        )

        assert tracker.session is not None
        assert tracker.session.session_id == "session_123"
        assert tracker.session.status == SessionStatus.ACTIVE
        assert tracker.session.context_usage == 0.3

    def test_update_session_status_existing(self, temp_state_file):
        """测试更新已有会话状态"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_session_status(
            session_id="session_123",
            status=SessionStatus.ACTIVE,
            context_usage=0.3
        )

        tracker.update_session_status(
            session_id="session_123",
            status=SessionStatus.IDLE,
            context_usage=0.0
        )

        assert tracker.session.status == SessionStatus.IDLE
        assert tracker.session.context_usage == 0.0

    def test_increment_restart_count(self, temp_state_file):
        """测试增加重启计数"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status(
            task_file="/tmp/task.md",
            status=TaskStatus.IN_PROGRESS
        )

        assert tracker.tasks["/tmp/task.md"].restart_count == 0

        tracker.increment_restart_count("/tmp/task.md")
        assert tracker.tasks["/tmp/task.md"].restart_count == 1

        tracker.increment_restart_count("/tmp/task.md")
        assert tracker.tasks["/tmp/task.md"].restart_count == 2

    def test_increment_restart_count_nonexistent(self, temp_state_file):
        """测试增加不存在任务的重启计数"""
        tracker = StateTracker(state_file=temp_state_file)

        # 不应该抛出异常
        tracker.increment_restart_count("/tmp/nonexistent.md")

    def test_get_task_state(self, temp_state_file):
        """测试获取任务状态"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status(
            task_file="/tmp/task.md",
            status=TaskStatus.PENDING
        )

        state = tracker.get_task_state("/tmp/task.md")
        assert state is not None
        assert state.task_file == "/tmp/task.md"

    def test_get_task_state_nonexistent(self, temp_state_file):
        """测试获取不存在的任务状态"""
        tracker = StateTracker(state_file=temp_state_file)

        state = tracker.get_task_state("/tmp/nonexistent.md")
        assert state is None

    def test_get_session_state(self, temp_state_file):
        """测试获取会话状态"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_session_status(
            session_id="session_123",
            status=SessionStatus.ACTIVE
        )

        state = tracker.get_session_state()
        assert state is not None
        assert state.session_id == "session_123"

    def test_get_session_state_none(self, temp_state_file):
        """测试获取空会话状态"""
        tracker = StateTracker(state_file=temp_state_file)

        state = tracker.get_session_state()
        assert state is None

    def test_get_all_tasks(self, temp_state_file):
        """测试获取所有任务"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status("/tmp/task1.md", TaskStatus.PENDING)
        tracker.update_task_status("/tmp/task2.md", TaskStatus.IN_PROGRESS)
        tracker.update_task_status("/tmp/task3.md", TaskStatus.COMPLETED)

        tasks = tracker.get_all_tasks()

        assert len(tasks) == 3
        assert "/tmp/task1.md" in tasks
        assert "/tmp/task2.md" in tasks
        assert "/tmp/task3.md" in tasks

    def test_get_pending_tasks(self, temp_state_file):
        """测试获取待处理任务"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status("/tmp/task1.md", TaskStatus.PENDING)
        tracker.update_task_status("/tmp/task2.md", TaskStatus.PENDING)
        tracker.update_task_status("/tmp/task3.md", TaskStatus.IN_PROGRESS)
        tracker.update_task_status("/tmp/task4.md", TaskStatus.COMPLETED)

        pending = tracker.get_pending_tasks()

        assert len(pending) == 2
        assert "/tmp/task1.md" in pending
        assert "/tmp/task2.md" in pending
        assert "/tmp/task3.md" not in pending

    def test_get_in_progress_tasks(self, temp_state_file):
        """测试获取进行中任务"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status("/tmp/task1.md", TaskStatus.PENDING)
        tracker.update_task_status("/tmp/task2.md", TaskStatus.IN_PROGRESS)
        tracker.update_task_status("/tmp/task3.md", TaskStatus.IN_PROGRESS)

        in_progress = tracker.get_in_progress_tasks()

        assert len(in_progress) == 2
        assert "/tmp/task2.md" in in_progress
        assert "/tmp/task3.md" in in_progress

    def test_clear_completed_tasks(self, temp_state_file):
        """测试清理已完成任务"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status("/tmp/task1.md", TaskStatus.PENDING)
        tracker.update_task_status("/tmp/task2.md", TaskStatus.COMPLETED)
        tracker.update_task_status("/tmp/task3.md", TaskStatus.IN_PROGRESS)
        tracker.update_task_status("/tmp/task4.md", TaskStatus.COMPLETED)

        tracker.clear_completed_tasks()

        assert len(tracker.tasks) == 2
        assert "/tmp/task1.md" in tracker.tasks
        assert "/tmp/task3.md" in tracker.tasks
        assert "/tmp/task2.md" not in tracker.tasks
        assert "/tmp/task4.md" not in tracker.tasks

    def test_export_report(self, temp_state_file):
        """测试导出报告"""
        tracker = StateTracker(state_file=temp_state_file)

        tracker.update_task_status("/tmp/task1.md", TaskStatus.PENDING)
        tracker.update_task_status("/tmp/task2.md", TaskStatus.IN_PROGRESS)
        tracker.update_task_status("/tmp/task3.md", TaskStatus.COMPLETED)
        tracker.update_task_status("/tmp/task4.md", TaskStatus.FAILED)

        tracker.update_session_status(
            session_id="session_123",
            status=SessionStatus.ACTIVE
        )

        report = tracker.export_report()

        assert "tasks" in report
        assert "session" in report
        assert "statistics" in report
        assert "generated_at" in report

        assert report["statistics"]["total_tasks"] == 4
        assert report["statistics"]["pending"] == 1
        assert report["statistics"]["in_progress"] == 1
        assert report["statistics"]["completed"] == 1
        assert report["statistics"]["failed"] == 1

    def test_persistence(self, temp_state_file):
        """测试状态持久化"""
        # 创建并更新追踪器
        tracker1 = StateTracker(state_file=temp_state_file)
        tracker1.update_task_status("/tmp/task.md", TaskStatus.IN_PROGRESS, progress=0.5)
        tracker1.update_session_status("session_123", SessionStatus.ACTIVE)

        # 重新加载
        tracker2 = StateTracker(state_file=temp_state_file)

        assert "/tmp/task.md" in tracker2.tasks
        assert tracker2.tasks["/tmp/task.md"].status == TaskStatus.IN_PROGRESS
        assert tracker2.tasks["/tmp/task.md"].progress == 0.5
        assert tracker2.session is not None
        assert tracker2.session.session_id == "session_123"


class TestStateTrackerEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def temp_state_file(self):
        """创建临时状态文件"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            yield f.name
        if os.path.exists(f.name):
            os.remove(f.name)

    def test_load_corrupted_file(self, temp_state_file):
        """测试加载损坏的文件"""
        # 写入无效 JSON
        with open(temp_state_file, 'w') as f:
            f.write("invalid json content")

        # 不应该抛出异常
        tracker = StateTracker(state_file=temp_state_file)

        assert tracker.tasks == {}
        assert tracker.session is None

    def test_load_partial_data(self, temp_state_file):
        """测试加载部分数据"""
        # 只有 tasks，没有 session
        data = {
            "tasks": {
                "/tmp/task.md": {
                    "task_file": "/tmp/task.md",
                    "status": "pending",
                    "progress": 0.0,
                    "started_at": None,
                    "completed_at": None,
                    "last_updated": None,
                    "error_message": None,
                    "restart_count": 0
                }
            }
        }

        with open(temp_state_file, 'w') as f:
            json.dump(data, f)

        tracker = StateTracker(state_file=temp_state_file)

        assert "/tmp/task.md" in tracker.tasks
        assert tracker.session is None

    def test_empty_tasks_list(self, temp_state_file):
        """测试空任务列表"""
        tracker = StateTracker(state_file=temp_state_file)

        assert tracker.get_pending_tasks() == []
        assert tracker.get_in_progress_tasks() == []
        assert tracker.get_all_tasks() == {}

    def test_export_report_empty(self, temp_state_file):
        """测试导出空报告"""
        tracker = StateTracker(state_file=temp_state_file)

        report = tracker.export_report()

        assert report["tasks"] == {}
        assert report["session"] is None
        assert report["statistics"]["total_tasks"] == 0
        assert report["statistics"]["pending"] == 0
