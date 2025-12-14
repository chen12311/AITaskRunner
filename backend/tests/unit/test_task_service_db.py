"""
Task Service Database Tests
测试任务服务数据库操作
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.services.task_service_db import TaskServiceDB
from backend.services.project_service import ProjectService
from backend.models.schemas import (
    TaskCreateRequest, TaskUpdateRequest,
    ProjectCreateRequest
)


@pytest.fixture
async def temp_project_with_doc(test_database):
    """创建带有临时目录和文档的测试项目"""
    project_service = ProjectService(db=test_database)

    # 创建临时目录和文档
    temp_dir = tempfile.mkdtemp()
    doc_path = Path(temp_dir) / "TEST_DOC.md"
    doc_path.write_text("# Test Document\n\n- [ ] Task 1\n- [ ] Task 2")

    # 创建项目
    request = ProjectCreateRequest(
        name="Test Project for Tasks",
        directory_path=temp_dir,
        description="A test project for task tests"
    )
    project = await project_service.create_project(request)

    yield {
        "project": project,
        "temp_dir": temp_dir,
        "doc_path": str(doc_path),
        "relative_doc_path": "/TEST_DOC.md"
    }

    # 清理
    if os.path.exists(str(doc_path)):
        os.unlink(str(doc_path))
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)


class TestTaskServiceCRUD:
    """测试任务 CRUD 操作"""

    @pytest.mark.asyncio
    async def test_create_task(self, test_database, temp_project_with_doc):
        """测试创建任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"],
            cli_type="claude_code"
        )

        task = await service.create_task(request)

        assert task is not None
        assert task.id is not None
        assert task.project_directory == project_data["temp_dir"]
        assert task.markdown_document_path == project_data["doc_path"]
        assert task.status == "pending"
        assert task.cli_type == "claude_code"

    @pytest.mark.asyncio
    async def test_create_task_with_callback(self, test_database, temp_project_with_doc):
        """测试创建带回调的任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"],
            callback_url="http://localhost:8080/callback"
        )

        task = await service.create_task(request)

        assert task is not None
        assert task.callback_url == "http://localhost:8080/callback"

    @pytest.mark.asyncio
    async def test_create_task_with_review_enabled(self, test_database, temp_project_with_doc):
        """测试创建启用审查的任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"],
            enable_review=True
        )

        task = await service.create_task(request)

        assert task is not None
        assert task.enable_review is True

    @pytest.mark.asyncio
    async def test_create_task_project_not_found(self, test_database):
        """测试创建任务时项目不存在"""
        service = TaskServiceDB(db=test_database)

        request = TaskCreateRequest(
            project_id="nonexistent_project_id",
            markdown_document_relative_path="/doc.md"
        )

        with pytest.raises(ValueError, match="Project not found"):
            await service.create_task(request)

    @pytest.mark.asyncio
    async def test_create_task_doc_not_found(self, test_database, temp_project_with_doc):
        """测试创建任务时文档不存在"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path="/nonexistent.md"
        )

        with pytest.raises(ValueError, match="文档不存在"):
            await service.create_task(request)

    @pytest.mark.asyncio
    async def test_get_task(self, test_database, temp_project_with_doc):
        """测试获取单个任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        created = await service.create_task(request)

        # 获取任务
        task = await service.get_task(created.id)

        assert task is not None
        assert task.id == created.id
        assert task.project_directory == project_data["temp_dir"]

    @pytest.mark.asyncio
    async def test_get_task_basic(self, test_database, temp_project_with_doc):
        """测试获取任务基本信息（不含日志）"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        created = await service.create_task(request)

        # 获取任务基本信息
        task = await service.get_task_basic(created.id)

        assert task is not None
        assert task.id == created.id
        # 基本信息不包含日志
        assert task.logs is None

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, test_database):
        """测试获取不存在的任务"""
        service = TaskServiceDB(db=test_database)

        task = await service.get_task("nonexistent_task_id")

        assert task is None

    @pytest.mark.asyncio
    async def test_get_all_tasks(self, test_database, temp_project_with_doc):
        """测试获取所有任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建多个任务
        for i in range(3):
            request = TaskCreateRequest(
                project_id=project_data["project"].id,
                markdown_document_relative_path=project_data["relative_doc_path"],
                cli_type="claude_code"
            )
            await service.create_task(request)

        # 获取所有任务
        tasks = await service.get_all_tasks()

        assert len(tasks) >= 3

    @pytest.mark.asyncio
    async def test_update_task_status(self, test_database, temp_project_with_doc):
        """测试更新任务状态"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        created = await service.create_task(request)

        # 更新任务状态
        update_request = TaskUpdateRequest(status="in_progress")
        updated = await service.update_task(created.id, update_request)

        assert updated is not None
        assert updated.status == "in_progress"

    @pytest.mark.asyncio
    async def test_update_task_cli_type(self, test_database, temp_project_with_doc):
        """测试更新任务 CLI 类型"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"],
            cli_type="claude_code"
        )
        created = await service.create_task(request)

        # 更新 CLI 类型
        update_request = TaskUpdateRequest(cli_type="codex")
        updated = await service.update_task(created.id, update_request)

        assert updated is not None
        assert updated.cli_type == "codex"

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, test_database):
        """测试更新不存在的任务"""
        service = TaskServiceDB(db=test_database)

        update_request = TaskUpdateRequest(status="in_progress")
        result = await service.update_task("nonexistent_id", update_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_task(self, test_database, temp_project_with_doc):
        """测试删除任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        created = await service.create_task(request)

        # 删除任务
        success = await service.delete_task(created.id)

        assert success is True

        # 验证任务已删除
        task = await service.get_task(created.id)
        assert task is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, test_database):
        """测试删除不存在的任务"""
        service = TaskServiceDB(db=test_database)

        success = await service.delete_task("nonexistent_id")

        assert success is False


class TestTaskStateTransitions:
    """测试任务状态流转"""

    @pytest.mark.asyncio
    async def test_pending_to_in_progress_to_completed(self, test_database, temp_project_with_doc):
        """测试 pending → in_progress → completed"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)
        assert task.status == "pending"

        # 启动任务
        success = await service.start_task(task.id)
        assert success is True
        task = await service.get_task(task.id)
        assert task.status == "in_progress"

        # 完成任务
        success = await service.complete_task(task.id)
        assert success is True
        task = await service.get_task(task.id)
        assert task.status == "completed"
        assert task.completed_at is not None

    @pytest.mark.asyncio
    async def test_pending_to_in_progress_to_failed(self, test_database, temp_project_with_doc):
        """测试 pending → in_progress → failed"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)
        assert task.status == "pending"

        # 启动任务
        success = await service.start_task(task.id)
        assert success is True
        task = await service.get_task(task.id)
        assert task.status == "in_progress"

        # 任务失败
        error_message = "Something went wrong"
        success = await service.fail_task(task.id, error_message)
        assert success is True
        task = await service.get_task(task.id)
        assert task.status == "failed"
        assert task.completed_at is not None

        # 验证错误日志
        logs = await service.get_task_logs(task.id)
        error_logs = [log for log in logs if log.level == "ERROR"]
        assert len(error_logs) > 0
        assert error_message in error_logs[-1].message

    @pytest.mark.asyncio
    async def test_pause_task(self, test_database, temp_project_with_doc):
        """测试暂停任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建并启动任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)
        await service.start_task(task.id)

        # 暂停任务
        success = await service.pause_task(task.id)
        assert success is True
        task = await service.get_task(task.id)
        assert task.status == "paused"

    @pytest.mark.asyncio
    async def test_start_task_and_return(self, test_database, temp_project_with_doc):
        """测试启动任务并返回"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)

        # 启动任务并返回
        updated_task = await service.start_task_and_return(task.id)
        assert updated_task is not None
        assert updated_task.status == "in_progress"

    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, test_database, temp_project_with_doc):
        """测试获取待处理任务"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建多个任务
        for i in range(3):
            request = TaskCreateRequest(
                project_id=project_data["project"].id,
                markdown_document_relative_path=project_data["relative_doc_path"]
            )
            await service.create_task(request)

        # 获取待处理任务
        pending_tasks = await service.get_pending_tasks()
        assert len(pending_tasks) >= 3

        # 所有任务状态应该是 pending 或 in_progress
        for task in pending_tasks:
            assert task.status in ["pending", "in_progress"]


class TestTaskLogs:
    """测试任务日志功能"""

    @pytest.mark.asyncio
    async def test_add_task_log(self, test_database, temp_project_with_doc):
        """测试添加任务日志"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)

        # 添加日志
        success = await service.add_task_log(task.id, "INFO", "Test log message", flush_immediately=True)
        assert success is True

        # 获取日志
        logs = await service.get_task_logs(task.id)
        assert len(logs) >= 1

        # 找到测试日志
        test_logs = [log for log in logs if log.message == "Test log message"]
        assert len(test_logs) == 1
        assert test_logs[0].level == "INFO"

    @pytest.mark.asyncio
    async def test_add_error_log_immediately(self, test_database, temp_project_with_doc):
        """测试错误日志立即写入"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)

        # 添加错误日志（应立即写入）
        success = await service.add_task_log(task.id, "ERROR", "Error message")
        assert success is True

        # 立即获取日志，错误日志应该已经存在
        logs = await service.get_task_logs(task.id)
        error_logs = [log for log in logs if log.level == "ERROR"]
        assert len(error_logs) >= 1

    @pytest.mark.asyncio
    async def test_get_task_logs_with_limit(self, test_database, temp_project_with_doc):
        """测试获取日志带限制"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)

        # 添加多条日志
        for i in range(5):
            await service.add_task_log(task.id, "INFO", f"Log message {i}", flush_immediately=True)

        # 获取日志带限制
        logs = await service.get_task_logs(task.id, limit=3)
        assert len(logs) <= 3

    @pytest.mark.asyncio
    async def test_flush_logs(self, test_database, temp_project_with_doc):
        """测试刷新日志缓冲"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)

        # 添加日志（不立即刷新）
        await service.add_task_log(task.id, "INFO", "Buffered log", flush_immediately=False)

        # 手动刷新
        await service.flush_logs()

        # 验证日志已写入
        logs = await service.get_task_logs(task.id)
        buffered_logs = [log for log in logs if log.message == "Buffered log"]
        assert len(buffered_logs) == 1


class TestTaskCallbacks:
    """测试任务回调通知"""

    @pytest.mark.asyncio
    async def test_complete_task_with_callback(self, test_database, temp_project_with_doc):
        """测试完成任务时发送回调"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建带回调的任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"],
            callback_url="http://localhost:8080/callback"
        )
        task = await service.create_task(request)

        # Mock 通知服务
        with patch.object(service.notification_service, 'notify_task_completed', new_callable=AsyncMock) as mock_notify:
            await service.complete_task(task.id)
            # 回调是异步创建的任务，需要等待一下
            import asyncio
            await asyncio.sleep(0.1)
            # 验证回调被调用
            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_fail_task_with_callback(self, test_database, temp_project_with_doc):
        """测试任务失败时发送回调"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建带回调的任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"],
            callback_url="http://localhost:8080/callback"
        )
        task = await service.create_task(request)

        # Mock 通知服务
        with patch.object(service.notification_service, 'notify_task_failed', new_callable=AsyncMock) as mock_notify:
            await service.fail_task(task.id, "Error occurred")
            # 回调是异步创建的任务，需要等待一下
            import asyncio
            await asyncio.sleep(0.1)
            # 验证回调被调用
            mock_notify.assert_called_once()


class TestTaskHelperMethods:
    """测试辅助方法"""

    @pytest.mark.asyncio
    async def test_get_task_raw(self, test_database, temp_project_with_doc):
        """测试获取任务原始数据"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)

        # 获取原始数据
        raw_task = await service.get_task_raw(task.id)
        assert raw_task is not None
        assert raw_task["id"] == task.id

    @pytest.mark.asyncio
    async def test_update_task_fields(self, test_database, temp_project_with_doc):
        """测试直接更新任务字段"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 创建任务
        request = TaskCreateRequest(
            project_id=project_data["project"].id,
            markdown_document_relative_path=project_data["relative_doc_path"]
        )
        task = await service.create_task(request)

        # 直接更新字段
        success = await service.update_task_fields(task.id, {"status": "completed"})
        assert success is True

        # 验证更新
        updated_task = await service.get_task(task.id)
        assert updated_task.status == "completed"


class TestPathValidation:
    """测试路径验证"""

    @pytest.mark.asyncio
    async def test_validate_nonexistent_directory(self, test_database):
        """测试项目目录不存在"""
        service = TaskServiceDB(db=test_database)

        with pytest.raises(ValueError, match="项目目录不存在"):
            service._validate_paths("/nonexistent/directory", "/nonexistent/directory/doc.md")

    @pytest.mark.asyncio
    async def test_validate_path_is_not_directory(self, test_database, temp_project_with_doc):
        """测试项目路径不是目录"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 使用文件作为目录
        with pytest.raises(ValueError, match="项目路径不是目录"):
            service._validate_paths(project_data["doc_path"], project_data["doc_path"])

    @pytest.mark.asyncio
    async def test_validate_doc_is_not_file(self, test_database, temp_project_with_doc):
        """测试文档路径不是文件"""
        service = TaskServiceDB(db=test_database)
        project_data = temp_project_with_doc

        # 使用目录作为文档
        with pytest.raises(ValueError, match="文档路径不是文件"):
            service._validate_paths(project_data["temp_dir"], project_data["temp_dir"])
