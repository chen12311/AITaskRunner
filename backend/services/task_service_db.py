"""
Task Service using SQLite database - 异步版本
"""
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import asyncio

from backend.database.models import Database, TaskDAO, ProjectDAO
from backend.models.schemas import (
    TaskModel, TaskLogModel,
    TaskCreateRequest, TaskUpdateRequest
)
from backend.services.notification_service import NotificationService


class TaskServiceDB:
    """Task service using SQLite database - 异步版本"""

    # 优化4.3: 日志缓冲配置
    LOG_BUFFER_SIZE = 10  # 缓冲区大小，达到此数量自动刷新
    LOG_BUFFER_TIMEOUT = 2.0  # 缓冲超时（秒），超时自动刷新

    def __init__(self, db_path: str = "aitaskrunner.db", db: Database = None):
        """
        初始化任务服务

        优化6.2: 支持注入共享数据库实例

        Args:
            db_path: 数据库文件路径（如果 db 为 None 时使用）
            db: 共享的数据库实例（优先使用）
        """
        if db is not None:
            self.db = db
        else:
            self.db = Database(db_path)
        self.task_dao = TaskDAO(self.db)
        self.project_dao = ProjectDAO(self.db)
        self.notification_service = NotificationService()
        self._initialized = False

        # 优化4.3: 日志缓冲区
        self._log_buffer: list = []
        self._log_buffer_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None

    def _validate_paths(self, project_directory: str, markdown_document_path: str) -> None:
        """
        验证项目目录和文档路径

        Args:
            project_directory: 项目目录路径
            markdown_document_path: Markdown 文档路径

        Raises:
            ValueError: 路径无效时抛出，包含详细错误信息
        """
        project_path = Path(project_directory)
        doc_path = Path(markdown_document_path)

        # 验证项目目录
        if not project_path.exists():
            raise ValueError(f"项目目录不存在: {project_directory}")
        if not project_path.is_dir():
            raise ValueError(f"项目路径不是目录: {project_directory}")

        # 验证文档路径
        if not doc_path.exists():
            # 尝试给出建议
            parent_dir = doc_path.parent
            if parent_dir.exists():
                similar_files = list(parent_dir.glob("*.md"))
                if similar_files:
                    suggestions = [f.name for f in similar_files[:5]]
                    raise ValueError(
                        f"文档不存在: {markdown_document_path}\n"
                        f"目录 {parent_dir} 下的 .md 文件: {', '.join(suggestions)}"
                    )
            raise ValueError(f"文档不存在: {markdown_document_path}")

        if not doc_path.is_file():
            raise ValueError(f"文档路径不是文件: {markdown_document_path}")

        # 验证文档是否在项目目录下（可选，但推荐）
        try:
            doc_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            # 文档不在项目目录下，给出警告但不阻止
            pass

    async def initialize(self):
        """初始化数据库"""
        if not self._initialized:
            await self.db.initialize()
            self._initialized = True

    async def get_all_tasks(self) -> List[TaskModel]:
        """获取所有任务"""
        await self.initialize()
        tasks = await self.task_dao.get_all_tasks()
        return [self._convert_to_model(task) for task in tasks]

    async def get_task(self, task_id: str) -> Optional[TaskModel]:
        """根据ID获取单个任务（含日志）"""
        await self.initialize()
        task = await self.task_dao.get_task(task_id)
        if task:
            return self._convert_to_model(task)
        return None

    async def get_task_basic(self, task_id: str) -> Optional[TaskModel]:
        """根据ID获取单个任务（不含日志，已优化）"""
        await self.initialize()
        task = await self.task_dao.get_task_basic(task_id)
        if task:
            return self._convert_to_model(task)
        return None

    async def create_task(self, request: TaskCreateRequest) -> TaskModel:
        """创建新任务"""
        await self.initialize()

        # 通过 project_id 获取项目目录
        project = await self.project_dao.get_project(request.project_id)
        if not project:
            raise ValueError(f"Project not found: {request.project_id}")

        project_directory = project['directory_path']

        # 拼接完整的文档路径
        relative_path = request.markdown_document_relative_path.lstrip('/')
        markdown_document_path = str(Path(project_directory) / relative_path)

        # 验证路径有效性
        self._validate_paths(project_directory, markdown_document_path)

        # 准备任务数据
        task_data = {
            'project_directory': project_directory,
            'markdown_document_path': markdown_document_path,
            'status': 'pending',
            'cli_type': request.cli_type or 'claude_code',
            'callback_url': request.callback_url,
            'enable_review': request.enable_review,
        }

        # 创建任务
        task_id = await self.task_dao.create_task(task_data)

        # 记录任务创建日志
        await self.task_dao.add_log(task_id, 'INFO', f'Task created for project: {project["name"]} ({project_directory})')

        # 返回创建的任务（不含日志以提升性能）
        return await self.get_task_basic(task_id)

    async def update_task(self, task_id: str, request: TaskUpdateRequest) -> Optional[TaskModel]:
        """更新任务"""
        await self.initialize()

        # 获取当前任务
        current_task = await self.get_task(task_id)
        if not current_task:
            return None

        updates = {}

        # 确定最终的项目目录（优先使用 project_id）
        final_project_dir = current_task.project_directory
        if request.project_id is not None:
            project = await self.project_dao.get_project(request.project_id)
            if not project:
                raise ValueError(f"Project not found: {request.project_id}")
            final_project_dir = project['directory_path']
            updates['project_directory'] = final_project_dir
        elif request.project_directory is not None:
            final_project_dir = request.project_directory
            updates['project_directory'] = request.project_directory

        final_doc_path = current_task.markdown_document_path

        # 处理相对路径更新
        if request.markdown_document_relative_path is not None:
            relative_path = request.markdown_document_relative_path.lstrip('/')
            final_doc_path = str(Path(final_project_dir) / relative_path)
            updates['markdown_document_path'] = final_doc_path

        # 如果更新了项目目录或文档路径，进行验证
        if 'project_directory' in updates or 'markdown_document_path' in updates:
            self._validate_paths(final_project_dir, final_doc_path)

        if request.status is not None:
            updates['status'] = request.status

        if request.cli_type is not None:
            updates['cli_type'] = request.cli_type

        if request.callback_url is not None:
            updates['callback_url'] = request.callback_url

        if request.enable_review is not None:
            updates['enable_review'] = request.enable_review

        if updates:
            success = await self.task_dao.update_task(task_id, updates)
            if success:
                await self.task_dao.add_log(task_id, 'INFO', f'Task updated: {", ".join(updates.keys())}')
                # 返回更新的任务（不含日志以提升性能）
                return await self.get_task_basic(task_id)

        return None

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        await self.initialize()
        return await self.task_dao.delete_task(task_id)

    async def get_pending_tasks(self) -> List[TaskModel]:
        """获取待处理任务"""
        await self.initialize()
        tasks = await self.task_dao.get_pending_tasks()
        return [self._convert_to_model(task) for task in tasks]

    async def start_task(self, task_id: str) -> bool:
        """标记任务为已开始"""
        await self.initialize()
        success = await self.task_dao.update_task(task_id, {'status': 'in_progress'})
        if success:
            await self.task_dao.add_log(task_id, 'INFO', 'Task started')
        return success

    async def start_task_and_return(self, task_id: str) -> Optional[TaskModel]:
        """标记任务为已开始并返回更新后的任务"""
        await self.initialize()
        success = await self.task_dao.update_task(task_id, {'status': 'in_progress'})
        if success:
            await self.task_dao.add_log(task_id, 'INFO', 'Task started')
            return await self.get_task_basic(task_id)
        return None

    async def pause_task(self, task_id: str) -> bool:
        """标记任务为已暂停"""
        await self.initialize()
        success = await self.task_dao.update_task(task_id, {'status': 'paused'})
        if success:
            await self.task_dao.add_log(task_id, 'INFO', 'Task paused')
        return success

    async def complete_task(self, task_id: str) -> bool:
        """标记任务为已完成"""
        await self.initialize()
        completed_at = datetime.now().isoformat()
        success = await self.task_dao.update_task(task_id, {
            'status': 'completed',
            'completed_at': completed_at
        })
        if success:
            await self.task_dao.add_log(task_id, 'INFO', 'Task completed')

            # 发送完成通知
            task = await self.get_task(task_id)
            if task and task.callback_url:
                asyncio.create_task(
                    self.notification_service.notify_task_completed(
                        callback_url=task.callback_url,
                        task_id=task_id,
                        project_directory=task.project_directory,
                        markdown_document_path=task.markdown_document_path
                    )
                )
        return success

    async def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务为失败"""
        await self.initialize()
        completed_at = datetime.now().isoformat()
        success = await self.task_dao.update_task(task_id, {
            'status': 'failed',
            'completed_at': completed_at
        })
        if success:
            await self.task_dao.add_log(task_id, 'ERROR', error_message)

            # 发送失败通知
            task = await self.get_task(task_id)
            if task and task.callback_url:
                asyncio.create_task(
                    self.notification_service.notify_task_failed(
                        callback_url=task.callback_url,
                        task_id=task_id,
                        project_directory=task.project_directory,
                        markdown_document_path=task.markdown_document_path,
                        error_message=error_message
                    )
                )
        return success

    async def add_task_log(self, task_id: str, level: str, message: str, flush_immediately: bool = False) -> bool:
        """
        优化4.3: 添加日志（支持缓冲）

        Args:
            task_id: 任务ID
            level: 日志级别
            message: 日志消息
            flush_immediately: 是否立即写入（用于关键日志，如错误）

        Returns:
            是否添加成功
        """
        await self.initialize()
        try:
            log_entry = {
                'task_id': task_id,
                'level': level,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }

            # 错误日志或明确要求立即写入
            if flush_immediately or level == 'ERROR':
                # 先刷新缓冲区，再写入当前日志
                await self._flush_log_buffer()
                await self.task_dao.add_log(task_id, level, message)
                return True

            async with self._log_buffer_lock:
                self._log_buffer.append(log_entry)

                # 缓冲区满，立即刷新
                if len(self._log_buffer) >= self.LOG_BUFFER_SIZE:
                    await self._flush_log_buffer_unlocked()
                else:
                    # 启动延迟刷新任务
                    self._schedule_flush()

            return True
        except Exception:
            return False

    async def _flush_log_buffer(self) -> None:
        """刷新日志缓冲区"""
        async with self._log_buffer_lock:
            await self._flush_log_buffer_unlocked()

    async def _flush_log_buffer_unlocked(self) -> None:
        """刷新日志缓冲区（内部方法，需要持有锁）"""
        if not self._log_buffer:
            return

        logs_to_write = self._log_buffer.copy()
        self._log_buffer.clear()

        # 取消定时刷新任务
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            self._flush_task = None

        try:
            await self.task_dao.add_logs_batch(logs_to_write)
        except Exception:
            # 批量写入失败时回退到逐条写入
            for log in logs_to_write:
                try:
                    await self.task_dao.add_log(
                        log['task_id'], log['level'], log['message']
                    )
                except Exception:
                    pass

    def _schedule_flush(self) -> None:
        """调度延迟刷新"""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._delayed_flush())

    async def _delayed_flush(self) -> None:
        """延迟刷新日志"""
        try:
            await asyncio.sleep(self.LOG_BUFFER_TIMEOUT)
            await self._flush_log_buffer()
        except asyncio.CancelledError:
            pass

    async def flush_logs(self) -> None:
        """公开的日志刷新方法（用于关闭时清理）"""
        await self._flush_log_buffer()

    async def get_task_logs(self, task_id: str, limit: int = 100) -> List[TaskLogModel]:
        """获取任务日志"""
        await self.initialize()
        logs = await self.task_dao.get_logs(task_id, limit)
        return [TaskLogModel(**log) for log in logs]

    async def get_task_raw(self, task_id: str) -> Optional[dict]:
        """获取任务原始数据（不含日志，用于内部逻辑）"""
        await self.initialize()
        return await self.task_dao.get_task_basic(task_id)

    async def update_task_fields(self, task_id: str, updates: dict) -> bool:
        """直接更新任务字段"""
        await self.initialize()
        return await self.task_dao.update_task(task_id, updates)

    def _convert_to_model(self, task_dict: dict) -> TaskModel:
        """将数据库字典转换为Pydantic模型"""
        logs = None
        if 'logs' in task_dict and task_dict['logs']:
            logs = [TaskLogModel(**log) for log in task_dict['logs']]

        # 处理 enable_review：数据库中 NULL->None, 0->False, 1->True
        enable_review_raw = task_dict.get('enable_review')
        enable_review = None if enable_review_raw is None else bool(enable_review_raw)

        return TaskModel(
            id=task_dict['id'],
            project_directory=task_dict['project_directory'],
            markdown_document_path=task_dict['markdown_document_path'],
            status=task_dict.get('status', 'pending'),
            cli_type=task_dict.get('cli_type', 'claude_code'),
            callback_url=task_dict.get('callback_url'),
            enable_review=enable_review,
            created_at=task_dict.get('created_at'),
            updated_at=task_dict.get('updated_at'),
            completed_at=task_dict.get('completed_at'),
            logs=logs
        )
