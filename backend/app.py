"""
FastAPI主应用 - 简化版本
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
_root_dir = Path(__file__).parent.parent
load_dotenv(_root_dir / ".env")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.models.schemas import (
    TaskModel, TaskCreateRequest, TaskUpdateRequest,
    TaskActionResponse, MonitorStatusResponse,
    TemplateModel, TemplateCreateRequest, TemplateUpdateRequest,
    ProjectModel, ProjectCreateRequest, ProjectUpdateRequest, ProjectLaunchRequest
)
from backend.services.codex_service import CodexService
from backend.services.task_service_db import TaskServiceDB
from backend.services.template_service import TemplateService
from backend.services.settings_service import SettingsService
from backend.services.project_service import ProjectService
from typing import List
import asyncio
from datetime import datetime
from pathlib import Path
import time

# 创建FastAPI应用
app = FastAPI(
    title="AITaskRunner API",
    description="AITaskRunner - AI编程助手自动化平台",
    version="2.0.0"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 优化9.1: 启用 Gzip 压缩
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)  # 响应 > 500 字节时压缩

# 优化6.1-6.3: 使用共享的数据库实例，减少连接数
from backend.database.shared import get_shared_database, close_shared_database

db_path = Path(__file__).parent.parent / "aitaskrunner.db"
shared_db = get_shared_database(str(db_path), pool_size=10)  # 共享连接池，大小为10

# 服务实例 - 所有服务共享同一个数据库连接池
settings_service = SettingsService(db=shared_db)
task_service = TaskServiceDB(db=shared_db)
codex_service = CodexService(settings_service=settings_service, task_service=task_service)
template_service = TemplateService(db=shared_db)
project_service = ProjectService(db=shared_db)

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    await codex_service.initialize()

    # 启动会话看门狗
    async def on_session_timeout(task_id: str, reason: str):
        """会话超时回调 - 通知前端"""
        await manager.broadcast({
            "type": "session_timeout",
            "data": {
                "task_id": task_id,
                "reason": reason,
                "message": "会话意外终止，正在自动恢复..."
            }
        })
    await codex_service.start_watchdog(on_timeout=on_session_timeout)

    # 优化4.4: 启动后台任务队列
    await background_queue.start()

    # 挂载静态文件目录（Docker 生产环境）
    static_dir = os.environ.get("STATIC_DIR")
    if static_dir and Path(static_dir).exists():
        app.mount("/assets", StaticFiles(directory=Path(static_dir) / "assets"), name="assets")

        # SPA 路由回退
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """SPA 路由回退到 index.html"""
            # API 路由不处理
            if full_path.startswith("api/") or full_path.startswith("ws/"):
                raise HTTPException(status_code=404)

            file_path = Path(static_dir) / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(Path(static_dir) / "index.html")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件 - 清理资源，确保 uvicorn reload 正常工作

    注意：热重载时不关闭终端会话，让 CLI 继续运行。
    只清理数据库连接等内部资源。
    """
    # 整体超时保护，避免关闭过程阻塞
    try:
        async def cleanup():
            # 注意：不再关闭终端会话！
            # 热重载时应该让终端会话继续运行，重启后重新连接
            active_count = codex_service.get_active_count()
            print(f"✅ 已停止所有 {active_count} 个会话")
            print("✅ 服务关闭：已清理所有 CLI 会话")

            # 优化4.3: 刷新日志缓冲区
            try:
                await task_service.flush_logs()
                print("✅ 服务关闭：已刷新日志缓冲区")
            except Exception as e:
                print(f"⚠️ 刷新日志缓冲区失败: {e}")

            # 优化4.4: 停止后台任务队列
            try:
                await background_queue.stop()
                print("✅ 服务关闭：已停止后台任务队列")
            except Exception as e:
                print(f"⚠️ 停止后台任务队列失败: {e}")

            # 停止会话看门狗
            try:
                await codex_service.stop_watchdog()
                print("✅ 服务关闭：已停止会话看门狗")
            except Exception as e:
                print(f"⚠️ 停止会话看门狗失败: {e}")

            # 优化6.3: 关闭共享数据库连接池（只需关闭一次）
            try:
                await close_shared_database()
                print("✅ 服务关闭：已关闭共享数据库连接池")
            except Exception as e:
                print(f"⚠️ 服务关闭时关闭数据库连接失败: {e}")

        await asyncio.wait_for(cleanup(), timeout=10.0)
    except asyncio.TimeoutError:
        print("⚠️ 服务关闭超时，强制退出")


# 优化4.4: 后台任务队列管理器
class BackgroundTaskQueue:
    """后台任务队列，用于管理会话重启等异步任务"""

    def __init__(self, max_concurrent: int = 3):
        self._queue: asyncio.Queue = None
        self._workers: List[asyncio.Task] = []
        self._pending_tasks: dict = {}  # task_id -> 是否有待处理任务
        self._running = False
        self._max_concurrent = max_concurrent
        self._lock = asyncio.Lock()

    async def start(self):
        """启动队列处理器"""
        if self._running:
            return
        self._running = True
        self._queue = asyncio.Queue()

        # 启动工作协程
        for i in range(self._max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

    async def stop(self):
        """停止队列处理器"""
        self._running = False

        # 发送停止信号
        for _ in self._workers:
            await self._queue.put(None)

        # 等待所有工作协程完成
        for worker in self._workers:
            try:
                await asyncio.wait_for(worker, timeout=5.0)
            except asyncio.TimeoutError:
                worker.cancel()

        self._workers.clear()
        self._pending_tasks.clear()

    async def enqueue(self, task_id: str, coro_func, *args, **kwargs):
        """
        将任务添加到队列

        Args:
            task_id: 任务ID（用于去重）
            coro_func: 协程函数
            *args, **kwargs: 传递给协程函数的参数
        """
        async with self._lock:
            # 避免同一任务重复入队
            if task_id in self._pending_tasks:
                return False

            self._pending_tasks[task_id] = True

        await self._queue.put((task_id, coro_func, args, kwargs))
        return True

    async def _worker(self, worker_id: int):
        """工作协程"""
        while self._running:
            try:
                item = await self._queue.get()
                if item is None:  # 停止信号
                    break

                task_id, coro_func, args, kwargs = item
                try:
                    await coro_func(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ 后台任务执行失败 [worker {worker_id}] task_id={task_id}: {e}")
                finally:
                    async with self._lock:
                        self._pending_tasks.pop(task_id, None)
                    self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ 后台任务工作协程异常 [worker {worker_id}]: {e}")


# 创建后台任务队列实例
background_queue = BackgroundTaskQueue(max_concurrent=3)


# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# ==================== 健康检查 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Codex Automation API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ==================== 初始化API (优化1.1) ====================

@app.get("/api/init")
async def get_init_data():
    """
    获取前端初始化所需的所有数据（优化1.1）
    合并 tasks + sessions + projects + settings 为单个请求
    """
    try:
        # 并行获取异步数据
        tasks, projects, settings = await asyncio.gather(
            task_service.get_all_tasks(),
            project_service.get_all_projects(),
            settings_service.get_all_settings()
        )

        # 同步获取会话数据（codex_service.get_all_sessions 是同步方法）
        sessions = codex_service.get_all_sessions()

        return {
            "tasks": tasks,
            "sessions": {
                "sessions": sessions,
                "count": len(sessions),
                "max_concurrent": codex_service.session_manager.max_concurrent
            },
            "projects": projects,
            "settings": {"settings": settings}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 任务管理API ====================

@app.get("/api/tasks")
async def get_all_tasks(page: int = None, page_size: int = None):
    """
    获取所有任务

    优化9.3: 支持分页（当任务数量 > 100 时建议使用）

    Args:
        page: 页码（从1开始，可选）
        page_size: 每页数量（默认50，最大100，可选）
    """
    try:
        tasks = await task_service.get_all_tasks()

        # 如果没有分页参数，返回所有任务（保持向后兼容）
        if page is None and page_size is None:
            return tasks

        # 分页处理
        page = max(1, page or 1)
        page_size = min(100, max(1, page_size or 50))
        total = len(tasks)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tasks = tasks[start:end]

        return {
            "tasks": paginated_tasks,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/pending", response_model=List[TaskModel])
async def get_pending_tasks():
    """获取待处理任务"""
    try:
        tasks = await task_service.get_pending_tasks()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}", response_model=TaskModel)
async def get_task(task_id: str):
    """获取单个任务详情"""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks", response_model=TaskModel)
async def create_task(request: TaskCreateRequest):
    """创建新任务"""
    try:
        task = await task_service.create_task(request)
        # 广播任务创建事件
        await manager.broadcast({
            "type": "task_created",
            "data": {"task_id": task.id}
        })
        return task
    except ValueError as e:
        # 路径验证失败，返回 400 错误和详细信息
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/tasks/{task_id}", response_model=TaskModel)
async def update_task(task_id: str, request: TaskUpdateRequest):
    """更新任务"""
    try:
        task = await task_service.update_task(task_id, request)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 广播更新事件
        await manager.broadcast({
            "type": "task_updated",
            "data": {"task_id": task_id}
        })

        return task
    except HTTPException:
        raise
    except ValueError as e:
        # 路径验证失败，返回 400 错误和详细信息
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/{task_id}", response_model=TaskActionResponse)
async def delete_task(task_id: str):
    """删除任务"""
    success = await task_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    # 广播删除事件
    await manager.broadcast({
        "type": "task_deleted",
        "data": {"task_id": task_id}
    })

    return TaskActionResponse(
        success=True,
        message=f"Task {task_id} deleted successfully",
        task_id=task_id
    )


# ==================== Codex会话控制API ====================

@app.post("/api/tasks/{task_id}/start")
async def start_task(task_id: str):
    """启动任务的 CLI 会话，返回更新后的任务数据"""
    task = await task_service.get_task_basic(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 检查是否有可用槽位
    available_slots = codex_service.get_available_slots()
    if available_slots <= 0:
        raise HTTPException(
            status_code=429,
            detail=f"Max concurrent sessions reached. Active: {codex_service.get_active_count()}, Max: {codex_service.session_manager.max_concurrent}"
        )

    # 优化4.2: 直接使用 task.status，无需额外调用 get_task_raw
    is_in_reviewing = task.status == 'in_reviewing'

    if is_in_reviewing:
        # 审查模式：使用审查 CLI 和审查模板
        review_cli_type = await settings_service.get_review_cli_type()
        api_base_url = await settings_service.get_setting('api_base_url') or 'http://127.0.0.1:8086'

        success = await codex_service.start_session(
            task_id=task_id,
            project_dir=task.project_directory,
            doc_path=task.markdown_document_path,
            api_base_url=api_base_url,
            cli_type=review_cli_type,
            template_name="review"
        )
    else:
        # 正常模式：使用任务配置的 CLI 和初始任务模板
        success = await codex_service.start_session(
            task_id=task_id,
            project_dir=task.project_directory,
            doc_path=task.markdown_document_path,
            cli_type=task.cli_type
        )

    if not success:
        await task_service.fail_task(task_id, "Failed to start CLI session")
        raise HTTPException(status_code=500, detail="Failed to start CLI session")

    # 更新任务状态并获取更新后的任务
    updated_task = await task_service.start_task_and_return(task_id)

    # 广播会话启动事件
    await manager.broadcast({
        "type": "session_started",
        "data": {
            "task_id": task_id,
            "active_sessions": codex_service.get_active_count()
        }
    })

    # 返回更新后的任务数据，供前端局部更新
    return {
        "success": True,
        "message": f"CLI session started for task {task_id}",
        "task_id": task_id,
        "task": updated_task
    }


@app.post("/api/tasks/{task_id}/pause", response_model=TaskActionResponse)
async def pause_task(task_id: str):
    """暂停任务"""
    await codex_service.stop_session(task_id)

    # 更新任务状态
    await task_service.pause_task(task_id)

    # 广播暂停事件
    await manager.broadcast({
        "type": "session_paused",
        "data": {"task_id": task_id}
    })

    return TaskActionResponse(
        success=True,
        message=f"Task {task_id} paused",
        task_id=task_id
    )


@app.post("/api/tasks/{task_id}/complete", response_model=TaskActionResponse)
async def complete_task(task_id: str):
    """标记任务完成"""
    success = await task_service.complete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    # 广播完成事件
    await manager.broadcast({
        "type": "task_completed",
        "data": {"task_id": task_id}
    })

    return TaskActionResponse(
        success=True,
        message=f"Task {task_id} marked as completed",
        task_id=task_id
    )


@app.post("/api/tasks/{task_id}/restart", response_model=TaskActionResponse)
async def restart_task(task_id: str):
    """重启任务会话"""
    try:
        await codex_service.restart_session(task_id)

        # 广播重启事件
        await manager.broadcast({
            "type": "session_restarted",
            "data": {"task_id": task_id}
        })

        return TaskActionResponse(
            success=True,
            message=f"Task {task_id} session restarted",
            task_id=task_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/set-callback", response_model=TaskActionResponse)
async def set_task_callback(task_id: str, request: dict):
    """设置任务的回调URL"""
    callback_url = request.get("callback_url")
    if not callback_url:
        raise HTTPException(status_code=400, detail="callback_url is required")

    update_request = TaskUpdateRequest(callback_url=callback_url)
    task = await task_service.update_task(task_id, update_request)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskActionResponse(
        success=True,
        message=f"Callback URL set for task {task_id}",
        task_id=task_id
    )


async def _restart_session_impl(task_id: str, task, progress: dict):
    """
    优化4.4: 会话重启的实际实现

    Args:
        task_id: 任务ID
        task: 任务对象
        progress: 进度信息字典
    """
    try:
        await task_service.add_task_log(task_id, "INFO", "重启会话中...")

        # 检查会话是否已在运行
        session_status = await codex_service.get_status(task_id)

        if session_status and session_status.is_running:
            # 会话已运行，直接发送继续执行指令
            await task_service.add_task_log(task_id, "INFO", "会话已运行，发送继续执行指令...")

            # 获取语言设置
            locale = await settings_service.get_language()

            # 渲染继续执行的模板消息
            continue_message = await template_service.render_template_async(
                "continue_task",
                locale=locale,
                project_dir=task.project_directory,
                doc_path=task.markdown_document_path,
                task_id=task_id,
                api_base_url=await settings_service.get_setting('api_base_url') or 'http://127.0.0.1:8086',
                remaining_tasks=progress['remaining']
            )

            await codex_service.send_message(continue_message, task_id)
            success = True  # send_message 没有返回值，假定发送成功
        else:
            # 会话未运行，启动新会话
            success = await codex_service.start_session(
                task_id=task_id,
                project_dir=task.project_directory,
                doc_path=task.markdown_document_path
            )

        if success:
            await task_service.add_task_log(task_id, "INFO", "✅ 会话重启成功，继续执行剩余任务")
            await manager.broadcast({
                "type": "session_restarted",
                "data": {
                    "task_id": task_id,
                    "remaining_tasks": progress['remaining']
                }
            })
        else:
            await task_service.add_task_log(task_id, "ERROR", "❌ 会话重启失败")
            await task_service.fail_task(task_id, "会话重启失败")
    except Exception as e:
        await task_service.add_task_log(task_id, "ERROR", f"❌ 重启会话异常: {e}")
        await task_service.fail_task(task_id, f"重启会话异常: {e}")


async def _create_restart_task(task_id: str, task, progress: dict, source: str = ""):
    """
    优化4.4: 将会话重启任务加入后台队列

    Args:
        task_id: 任务ID
        task: 任务对象
        progress: 进度信息字典
        source: 来源标识（用于日志）
    """
    # 使用后台队列，避免重复入队
    enqueued = await background_queue.enqueue(
        task_id,
        _restart_session_impl,
        task_id, task, progress
    )
    if not enqueued:
        await task_service.add_task_log(task_id, "INFO", "重启任务已在队列中，跳过重复入队")


async def _should_enable_review(task_id: str) -> bool:
    """
    检查是否应该启用 Review 审查

    优先级: 任务级设置 > 全局设置
    """
    task_data = await task_service.get_task_raw(task_id)
    if task_data is None:
        return False

    # 任务级设置优先（enable_review: NULL=继承, 0=禁用, 1=启用）
    enable_review = task_data.get('enable_review')
    if enable_review is not None:
        return bool(enable_review)

    # 继承全局设置
    return await settings_service.get_review_enabled()


async def _complete_task_with_cleanup(task_id: str, log_message: str):
    """
    完成任务并清理会话资源

    Args:
        task_id: 任务ID
        log_message: 完成日志消息
    """
    await task_service.complete_task(task_id)
    await codex_service.stop_session(task_id)
    # 清除看门狗心跳记录
    if codex_service.watchdog:
        codex_service.watchdog.clear_activity(task_id)
    await task_service.add_task_log(task_id, "INFO", log_message)
    await manager.broadcast({
        "type": "task_completed",
        "data": {"task_id": task_id}
    })


async def _trigger_review_task(task_id: str, task):
    """
    触发 Review 任务 - 使用不同的 CLI 进行交叉审查

    Args:
        task_id: 任务ID
        task: 任务对象
    """
    # 检查是否启用 review
    if not await _should_enable_review(task_id):
        # Review 未启用，直接标记任务完成
        await _complete_task_with_cleanup(task_id, "✅ 任务完成（Review 未启用）")
        return

    # 设置 in_reviewing 状态
    await task_service.update_task_fields(task_id, {'status': 'in_reviewing'})

    # 获取 review CLI 类型
    review_cli_type = await settings_service.get_review_cli_type()
    current_cli_type = await settings_service.get_cli_type()

    await task_service.add_task_log(
        task_id, "INFO",
        f"🔍 开始执行 Review 审查（切换 CLI: {current_cli_type} → {review_cli_type}）"
    )

    # 获取 API 基础地址
    api_base_url = await settings_service.get_setting('api_base_url') or 'http://localhost:8000'

    # 彻底移除旧会话（避免看门狗误判 STARTING 状态）
    await codex_service.remove_session(task_id)

    # 使用 review CLI 启动全新会话（直接使用 review 模板）
    success = await codex_service.start_session(
        task_id=task_id,
        project_dir=task.project_directory,
        doc_path=task.markdown_document_path,
        api_base_url=api_base_url,
        cli_type=review_cli_type,
        template_name="review"  # 使用 review 模板而不是 initial_task
    )

    if not success:
        await task_service.add_task_log(task_id, "ERROR", f"❌ 启动 Review CLI ({review_cli_type}) 失败")
        # 回滚状态为 in_progress
        await task_service.update_task_fields(task_id, {'status': 'in_progress'})
        return

    await task_service.add_task_log(task_id, "INFO", f"已使用 {review_cli_type} 启动 Review 会话")

    # 广播状态更新
    await manager.broadcast({
        "type": "review_started",
        "data": {
            "task_id": task_id,
            "cli_type": review_cli_type,
            "message": f"Review phase started with {review_cli_type}"
        }
    })


@app.post("/api/tasks/{task_id}/notify-status")
async def notify_task_status(task_id: str, request: dict):
    """
    供 Claude Code 调用的接口 - 通知任务状态

    请求体:
    {
        "status": "completed" | "failed" | "in_progress" | "session_completed" | "review_completed" | "review_session_completed",
        "message": "可选的状态消息",
        "error": "可选的错误信息（仅在 failed 时）"
    }

    状态说明:
    - completed / session_completed: 任务完成，会自动触发 review 阶段
    - review_completed: review 审查通过，任务最终完成
    - review_session_completed: review 会话完成但需要继续，会重启会话
    - failed: 任务失败
    - in_progress: 任务进行中
    """
    # 记录心跳（看门狗用于检测会话存活）
    if codex_service.watchdog:
        codex_service.watchdog.record_activity(task_id)

    status = request.get("status")
    message = request.get("message", "")
    error = request.get("error")

    if not status:
        raise HTTPException(status_code=400, detail="status is required")

    # 验证任务存在
    task = await task_service.get_task_basic(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 记录日志
    log_level = "ERROR" if status == "failed" else "INFO"
    log_message = f"Status update from Claude Code: {status}"
    if message:
        log_message += f" - {message}"
    await task_service.add_task_log(task_id, log_level, log_message)

    # 根据状态更新任务
    if status == "session_completed":
        # 会话完成，检查是否还有剩余任务
        from backend.utils.markdown_checker import check_remaining_tasks, get_task_progress_summary

        progress = check_remaining_tasks(task.markdown_document_path)
        progress_summary = f"{progress['completed']}/{progress['total']} completed ({progress['remaining']} remaining)"

        await task_service.add_task_log(task_id, "INFO", f"会话完成，检查任务进度: {progress_summary}")

        if progress.get("has_remaining", False):
            # 还有未完成任务，准备重启会话
            await task_service.add_task_log(
                task_id,
                "INFO",
                f"检测到 {progress['remaining']} 个未完成任务，准备重启会话继续执行"
            )
            await _create_restart_task(task_id, task, progress)
            response_message = f"Session completed, restarting for {progress['remaining']} remaining tasks"
        else:
            # 优化4.2: 直接使用 task.status，无需再次查询
            if task.status == 'in_reviewing':
                # 已在 review 阶段，标记最终完成
                await _complete_task_with_cleanup(task_id, "✅ Review 通过，任务最终完成")
                response_message = "Review completed, all tasks finished"
            else:
                # 触发 review
                await _trigger_review_task(task_id, task)
                response_message = "All tasks done, starting review phase"

    elif status == "completed":
        # 强制验证文档完成率
        from backend.utils.markdown_checker import check_remaining_tasks

        progress = check_remaining_tasks(task.markdown_document_path)
        progress_summary = f"{progress['completed']}/{progress['total']} completed ({progress['remaining']} remaining)"

        if progress.get("has_remaining", False):
            # 还有未完成任务，自动转为 session_completed 逻辑
            await task_service.add_task_log(
                task_id,
                "WARNING",
                f"⚠️ Codex 发送 completed 但文档还有 {progress['remaining']} 个未完成任务（{progress_summary}），自动转为 session_completed 继续执行"
            )
            await _create_restart_task(task_id, task, progress)
            response_message = f"Detected {progress['remaining']} remaining tasks, converted to session_completed and restarting"
        else:
            # 优化4.2: 直接使用 task.status，无需再次查询
            if task.status == 'in_reviewing':
                # 已在 review 阶段，标记最终完成
                await _complete_task_with_cleanup(task_id, f"✅ Review 通过，任务最终完成（{progress_summary}）")
                response_message = "Review completed, all tasks finished"
            else:
                # 触发 review
                await _trigger_review_task(task_id, task)
                response_message = f"All tasks done ({progress_summary}), starting review phase"

    elif status == "review_completed":
        # 优化4.2: 直接使用 task.status
        if task.status != 'in_reviewing':
            await task_service.add_task_log(
                task_id,
                "WARNING",
                "⚠️ 收到 review_completed 但任务未处于 review 阶段"
            )
            raise HTTPException(status_code=400, detail="Task is not in review phase")

        # 标记任务最终完成
        await _complete_task_with_cleanup(task_id, "✅ Review 通过，任务最终完成")
        response_message = "Review completed, task finished"

    elif status == "review_session_completed":
        # 优化4.2: 直接使用 task.status
        if task.status != 'in_reviewing':
            await task_service.add_task_log(
                task_id,
                "WARNING",
                "⚠️ 收到 review_session_completed 但任务未处于 review 阶段"
            )
            raise HTTPException(status_code=400, detail="Task is not in review phase")

        await task_service.add_task_log(
            task_id,
            "INFO",
            "Review 会话完成，准备重启继续审查"
        )

        # 重启会话继续 review
        await _trigger_review_task(task_id, task)
        response_message = "Review session completed, restarting to continue"

    elif status == "failed":
        error_msg = error or message or "Task failed"
        await task_service.fail_task(task_id, error_msg)
        response_message = "Task marked as failed"
    elif status == "in_progress":
        await task_service.start_task(task_id)

        # 检查是否还有剩余任务需要继续执行
        from backend.utils.markdown_checker import check_remaining_tasks

        progress = check_remaining_tasks(task.markdown_document_path)
        progress_summary = f"{progress['completed']}/{progress['total']} completed ({progress['remaining']} remaining)"

        await task_service.add_task_log(task_id, "INFO", f"进度更新: {progress_summary}")

        if progress.get("has_remaining", False):
            # 还有未完成任务，准备重启会话继续执行
            await task_service.add_task_log(
                task_id,
                "INFO",
                f"检测到 {progress['remaining']} 个未完成任务，准备重启会话继续执行"
            )
            await _create_restart_task(task_id, task, progress)
            response_message = f"Task in progress, restarting for {progress['remaining']} remaining tasks"
        else:
            # 优化4.2: 直接使用 task.status
            if task.status == 'in_reviewing':
                # 已在 review 阶段，标记最终完成
                await _complete_task_with_cleanup(task_id, "✅ Review 通过，任务最终完成")
                response_message = "Review completed, all tasks finished"
            else:
                # 触发 review
                await _trigger_review_task(task_id, task)
                response_message = "All tasks done, starting review phase"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    # 广播状态更新
    await manager.broadcast({
        "type": "task_status_updated",
        "data": {
            "task_id": task_id,
            "status": status,
            "message": message
        }
    })

    return {
        "success": True,
        "message": response_message,
        "task_id": task_id,
        "status": status
    }


# ==================== 会话管理API ====================

@app.get("/api/sessions")
async def get_all_sessions():
    """获取所有会话状态"""
    try:
        sessions = codex_service.get_all_sessions()
        return {
            "sessions": sessions,
            "total": len(sessions),
            "active": codex_service.get_active_count(),
            "max_concurrent": codex_service.session_manager.max_concurrent,
            "available_slots": codex_service.get_available_slots()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/active")
async def get_active_sessions():
    """获取所有活跃会话"""
    try:
        sessions = codex_service.get_active_sessions()
        return {
            "sessions": sessions,
            "count": len(sessions),
            "max_concurrent": codex_service.session_manager.max_concurrent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{task_id}")
async def get_session_status(task_id: str):
    """获取指定会话状态"""
    try:
        session = await codex_service.get_session_status(task_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session for task {task_id} not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{task_id}")
async def remove_session(task_id: str):
    """移除指定会话"""
    try:
        success = await codex_service.remove_session(task_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session for task {task_id} not found")
        return {"success": True, "message": f"Session {task_id} removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/stop-all")
async def stop_all_sessions():
    """停止所有会话"""
    try:
        await codex_service.stop_all_sessions()
        return {"success": True, "message": "All sessions stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 监控API ====================

@app.get("/api/monitor/status", response_model=MonitorStatusResponse)
async def get_monitor_status():
    """获取系统监控状态"""
    try:
        # 获取Codex状态
        codex_status = await codex_service.get_status()

        # 获取当前任务
        current_task = None
        if codex_status.current_task_id:
            current_task = await task_service.get_task(codex_status.current_task_id)

        # 获取待处理任务数量
        pending_tasks = await task_service.get_pending_tasks()

        return MonitorStatusResponse(
            codex_status=codex_status,
            current_task=current_task,
            pending_tasks_count=len(pending_tasks)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitor/send-message")
async def send_message_to_codex(message: dict):
    """发送消息给Codex"""
    try:
        await codex_service.send_message(message.get("content", ""))
        return {"success": True, "message": "Message sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket实时通信 ====================

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    优化7.1-7.3: WebSocket端点 - 实时推送监控数据和活跃会话
    统一推送，前端无需轮询
    """
    await manager.connect(websocket)

    try:
        # 启动后台任务,定期推送状态
        async def push_status():
            while True:
                try:
                    # 获取 codex 状态
                    status = await codex_service.get_status()

                    # 优化7.1: 同时推送活跃会话列表
                    sessions = await codex_service.get_all_sessions()

                    await websocket.send_json({
                        "type": "status_update",
                        "data": {
                            "is_running": status.is_running,
                            "context_usage": status.context_usage,
                            "context_tokens": status.context_tokens,
                            "max_tokens": status.max_tokens,
                            "current_task_id": status.current_task_id,
                            "timestamp": datetime.now().isoformat(),
                            # 新增：活跃会话数据
                            "sessions": {
                                "sessions": sessions,
                                "count": len(sessions),
                                "max_concurrent": codex_service.session_manager.max_concurrent
                            }
                        }
                    })
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"WebSocket推送错误: {e}")
                    break

        push_task = asyncio.create_task(push_status())

        while True:
            data = await websocket.receive_text()
            print(f"收到WebSocket消息: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        push_task.cancel()
        print("WebSocket连接断开")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        manager.disconnect(websocket)


# ==================== 日志API ====================

@app.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: str, limit: int = 100):
    """获取任务日志"""
    try:
        logs = await task_service.get_task_logs(task_id, limit)
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 模板管理API ====================

@app.get("/api/templates", response_model=List[TemplateModel])
async def get_all_templates():
    """获取所有模板"""
    try:
        templates = await template_service.get_all_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates/type/{template_type}", response_model=List[TemplateModel])
async def get_templates_by_type(template_type: str):
    """获取指定类型的所有模板"""
    try:
        templates = await template_service.get_templates_by_type(template_type)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates/{template_id}", response_model=TemplateModel)
async def get_template(template_id: str):
    """获取单个模板"""
    template = await template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@app.post("/api/templates", response_model=TemplateModel)
async def create_template(request: TemplateCreateRequest):
    """创建新模板"""
    try:
        template = await template_service.create_template(request)
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/templates/{template_id}", response_model=TemplateModel)
async def update_template(template_id: str, request: TemplateUpdateRequest):
    """更新模板"""
    try:
        template = await template_service.update_template(template_id, request)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    """删除模板"""
    success = await template_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "message": f"Template {template_id} deleted"}


@app.post("/api/templates/{template_id}/set-default")
async def set_default_template(template_id: str):
    """设置默认模板"""
    success = await template_service.set_default_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "message": f"Template {template_id} set as default"}


@app.post("/api/templates/render")
async def render_template(request: dict):
    """渲染模板（预览）"""
    try:
        template_type = request.get("type")
        locale = request.get("locale", "zh")  # 默认中文
        variables = request.get("variables", {})
        content = await template_service.render_template(template_type, locale=locale, **variables)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 项目管理API ====================

@app.get("/api/projects", response_model=List[ProjectModel])
async def get_all_projects():
    """获取所有项目"""
    try:
        projects = await project_service.get_all_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}", response_model=ProjectModel)
async def get_project(project_id: str):
    """获取单个项目"""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/api/projects", response_model=ProjectModel)
async def create_project(request: ProjectCreateRequest):
    """创建新项目"""
    try:
        project = await project_service.create_project(request)
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_id}", response_model=ProjectModel)
async def update_project(project_id: str, request: ProjectUpdateRequest):
    """更新项目"""
    try:
        project = await project_service.update_project(project_id, request)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    success = await project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "message": f"Project {project_id} deleted"}


@app.post("/api/projects/{project_id}/launch")
async def launch_project(project_id: str, request: ProjectLaunchRequest = None):
    """
    一键启动项目终端

    启动模式:
    - cli: 打开终端并启动默认CLI工具（如 claude）
    - terminal: 仅打开终端并进入项目目录
    """
    # 获取项目信息
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = project.directory_path
    if not project_dir:
        raise HTTPException(status_code=400, detail="Project directory not configured")

    # 检查目录是否存在
    if not os.path.isdir(project_dir):
        raise HTTPException(status_code=400, detail=f"Project directory does not exist: {project_dir}")

    # 确定要执行的命令
    if request is None:
        request = ProjectLaunchRequest()

    if request.command:
        # 使用自定义命令
        command = request.command
    elif request.mode == "terminal":
        # 仅打开终端，不执行命令
        command = ""
    else:
        # 使用默认CLI
        default_cli = await settings_service.get_setting("default_cli")
        cli_commands = {
            "claude_code": "claude",
            "codex": "codex",
            "gemini": "gemini",
            "aider": "aider",
            "cursor": "cursor"
        }
        command = cli_commands.get(default_cli, "claude")

    # 获取终端适配器（支持指定终端类型）
    terminal_type = request.terminal if request.terminal else None
    terminal_adapter = await codex_service.get_terminal_adapter(terminal_type)
    if not terminal_adapter:
        raise HTTPException(status_code=500, detail="No terminal adapter available")

    # 创建终端窗口
    try:
        session = await terminal_adapter.create_window(
            project_dir=project_dir,
            command=command
        )

        if session:
            return {
                "success": True,
                "message": f"Terminal launched for project: {project.name}",
                "session_id": session.session_id,
                "command": command or "(none)",
                "project_directory": project_dir
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create terminal window")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch terminal: {str(e)}")


# ==================== 系统设置API ====================

@app.get("/api/settings")
async def get_all_settings():
    """获取所有系统设置"""
    try:
        settings = await settings_service.get_all_settings()
        return {"settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/{key}")
async def get_setting(key: str):
    """获取单个设置"""
    try:
        value = await settings_service.get_setting(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
        return {"key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/settings/{key}")
async def update_setting(key: str, request: dict):
    """更新单个设置"""
    try:
        value = request.get("value")
        if value is None:
            raise HTTPException(status_code=400, detail="value is required")

        # 特殊处理终端类型设置
        if key == "terminal":
            supported = await settings_service.get_supported_terminals()
            if value not in supported:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid terminal type: {value}. Supported: {', '.join(supported)}"
                )
            # 通知 CodexService 更新终端适配器
            await codex_service.update_terminal_adapter()

        # 特殊处理 CLI 类型设置
        if key == "default_cli":
            if value not in ["claude_code", "codex", "gemini"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid CLI type: {value}. Supported: claude_code, codex, gemini"
                )
            # 通知 CodexService 更新 CLI 适配器
            await codex_service.update_cli_adapter(value)

        success = await settings_service.set_setting(key, value)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save setting")

        return {"success": True, "key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/terminal/available")
async def get_available_terminals():
    """获取可用的终端列表（根据平台自动检测）"""
    try:
        import platform
        from core.terminal_adapters import (
            KittyAdapter,
            iTermAdapter,
            WindowsTerminalAdapter,
            get_available_terminal_adapters
        )

        system = platform.system()
        terminals = []

        # 总是添加 auto 选项
        terminals.append({
            "id": "auto",
            "name": "auto",
            "installed": True,
            "recommended": True
        })

        # 根据平台添加可用终端
        if system == "Darwin":  # macOS
            kitty = KittyAdapter()
            terminals.append({
                "id": "kitty",
                "name": "kitty",
                "installed": kitty.is_available(),
                "recommended": False
            })

            iterm = iTermAdapter()
            terminals.append({
                "id": "iterm",
                "name": "iterm",
                "installed": iterm.is_available(),
                "recommended": False
            })

        elif system == "Linux":
            kitty = KittyAdapter()
            terminals.append({
                "id": "kitty",
                "name": "kitty",
                "installed": kitty.is_available(),
                "recommended": False
            })

        elif system == "Windows":
            wt = WindowsTerminalAdapter()
            terminals.append({
                "id": "windows_terminal",
                "name": "windows_terminal",
                "installed": wt.is_available(),
                "recommended": False
            })

        current = await settings_service.get_terminal_type()

        return {
            "terminals": terminals,
            "current": current,
            "platform": system
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/cli/available")
async def get_available_cli_tools():
    """获取可用的 CLI 工具列表"""
    try:
        from core.cli_adapters import get_available_cli_types, get_cli_adapter

        cli_tools = []

        # Claude Code
        try:
            claude_adapter = get_cli_adapter("claude_code")
            cli_tools.append({
                "id": "claude_code",
                "name": "claude_code",
                "installed": claude_adapter.is_available(),
                "recommended": True,
                "supports_status": True,
                "supports_resume": False
            })
        except Exception:
            cli_tools.append({
                "id": "claude_code",
                "name": "claude_code",
                "installed": False,
                "recommended": True,
                "supports_status": True,
                "supports_resume": False
            })

        # OpenAI Codex CLI
        try:
            codex_adapter = get_cli_adapter("codex")
            cli_tools.append({
                "id": "codex",
                "name": "codex",
                "installed": codex_adapter.is_available(),
                "recommended": False,
                "supports_status": False,
                "supports_resume": True
            })
        except Exception:
            cli_tools.append({
                "id": "codex",
                "name": "codex",
                "installed": False,
                "recommended": False,
                "supports_status": False,
                "supports_resume": True
            })

        # Google Gemini CLI
        try:
            gemini_adapter = get_cli_adapter("gemini")
            cli_tools.append({
                "id": "gemini",
                "name": "gemini",
                "installed": gemini_adapter.is_available(),
                "recommended": False,
                "supports_status": False,
                "supports_resume": True
            })
        except Exception:
            cli_tools.append({
                "id": "gemini",
                "name": "gemini",
                "installed": False,
                "recommended": False,
                "supports_status": False,
                "supports_resume": True
            })

        current = await settings_service.get_cli_type()

        return {
            "cli_tools": cli_tools,
            "current": current
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/cli/review/available")
async def get_available_review_cli_tools():
    """获取可用的 Review CLI 工具列表"""
    try:
        from core.cli_adapters import get_cli_adapter

        cli_tools = []

        # Claude Code
        try:
            claude_adapter = get_cli_adapter("claude_code")
            cli_tools.append({
                "id": "claude_code",
                "name": "claude_code",
                "installed": claude_adapter.is_available(),
                "recommended": False,
                "supports_status": True,
                "supports_session_recovery": False
            })
        except Exception:
            cli_tools.append({
                "id": "claude_code",
                "name": "claude_code",
                "installed": False,
                "recommended": False,
                "supports_status": True,
                "supports_session_recovery": False
            })

        # OpenAI Codex CLI
        try:
            codex_adapter = get_cli_adapter("codex")
            cli_tools.append({
                "id": "codex",
                "name": "codex",
                "installed": codex_adapter.is_available(),
                "recommended": True,
                "supports_status": False,
                "supports_session_recovery": True
            })
        except Exception:
            cli_tools.append({
                "id": "codex",
                "name": "codex",
                "installed": False,
                "recommended": True,
                "supports_status": False,
                "supports_session_recovery": True
            })

        # Google Gemini CLI
        try:
            gemini_adapter = get_cli_adapter("gemini")
            cli_tools.append({
                "id": "gemini",
                "name": "gemini",
                "installed": gemini_adapter.is_available(),
                "recommended": False,
                "supports_status": False,
                "supports_session_recovery": True
            })
        except Exception:
            cli_tools.append({
                "id": "gemini",
                "name": "gemini",
                "installed": False,
                "recommended": False,
                "supports_status": False,
                "supports_session_recovery": True
            })

        current = await settings_service.get_review_cli_type()

        return {
            "cli_tools": cli_tools,
            "current": current
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    from urllib.parse import urlparse

    # 从 API_BASE_URL 解析端口
    api_base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:8086")
    parsed = urlparse(api_base_url)
    port = parsed.port or 8086

    print(f"🚀 启动后端服务: {api_base_url}")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
