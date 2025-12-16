"""
会话看门狗 - 监控会话健康状态，自动恢复意外终止的会话
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Set, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from core.session.manager import SessionManager
    from core.session.models import ManagedSession


class SessionWatchdog:
    """
    会话看门狗 - 监控会话健康状态

    检测逻辑：
    1. 终端窗口不存在 → terminated（自动重启会话）
    2. Kitty: at_prompt=true → idle（发送恢复消息唤醒 CLI）

    注意：仅 Kitty 终端支持 idle 检测，其他终端只检测 terminated
    """

    def __init__(
        self,
        session_manager: "SessionManager",
        task_service=None,
        heartbeat_timeout: float = 300.0,
        check_interval: float = 30.0,
        on_timeout: Optional[Callable] = None
    ):
        """
        Args:
            session_manager: 会话管理器
            task_service: 任务服务（用于查询任务状态）
            heartbeat_timeout: 心跳超时时间（秒），默认5分钟
            check_interval: 检查间隔（秒），默认30秒
            on_timeout: 超时回调函数 async def callback(task_id, reason)
        """
        self._session_manager = session_manager
        self._task_service = task_service
        self._heartbeat_timeout = heartbeat_timeout
        self._check_interval = check_interval
        self._on_timeout = on_timeout

        self._last_activity: Dict[str, datetime] = {}
        self._safe_transition_tasks: Set[str] = set()  # 正在安全转换期的任务
        self._watchdog_task: Optional[asyncio.Task] = None
        self._running = False

    def record_activity(self, task_id: str):
        """记录任务活动（收到回调时调用）"""
        self._last_activity[task_id] = datetime.now()

    def clear_activity(self, task_id: str):
        """清除任务活动记录（任务完成/移除时调用）"""
        self._last_activity.pop(task_id, None)

    def begin_safe_transition(self, task_id: str):
        """标记任务进入安全转换期（会话正常切换时调用，避免看门狗误判）"""
        self._safe_transition_tasks.add(task_id)

    def end_safe_transition(self, task_id: str):
        """标记任务退出安全转换期"""
        self._safe_transition_tasks.discard(task_id)

    @asynccontextmanager
    async def safe_transition(self, task_id: str):
        """
        安全转换期上下文管理器

        用法:
            async with watchdog.safe_transition(task_id):
                await remove_session(task_id)
                await start_session(task_id, ...)
        """
        self.begin_safe_transition(task_id)
        try:
            yield
        finally:
            self.end_safe_transition(task_id)

    async def start(self):
        """启动看门狗"""
        if self._running:
            return
        self._running = True
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())
        print(f"🐕 会话看门狗已启动 (超时: {self._heartbeat_timeout}s, 间隔: {self._check_interval}s)")

    async def stop(self):
        """停止看门狗"""
        self._running = False
        if self._watchdog_task:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
            self._watchdog_task = None
        print("🐕 会话看门狗已停止")

    async def _watchdog_loop(self):
        """监控主循环"""
        while self._running:
            try:
                await asyncio.sleep(self._check_interval)
                await self._check_all_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ 看门狗异常: {e}")
                await asyncio.sleep(60)

    async def _check_all_sessions(self):
        """检查所有活跃会话"""
        active_sessions = self._session_manager.get_active_sessions()

        for session in active_sessions:
            task_id = session.task_id

            # 跳过正在安全转换期的任务（正常的会话切换，非意外终止）
            if task_id in self._safe_transition_tasks:
                continue

            health = await self._check_session_health(task_id, session)

            if health == "terminated":
                await self._handle_terminated(task_id, session)
            elif health == "idle":
                await self._handle_idle(task_id, session)

    async def _check_session_health(self, task_id: str, session: "ManagedSession") -> str:
        """
        检查会话健康状态

        检测逻辑：
        1. 终端窗口是否存活
        2. 终端原生活跃检测（仅 Kitty 支持）

        Returns:
            "healthy" - 正常
            "idle" - CLI 不活跃（需要发送恢复消息，仅 Kitty）
            "terminated" - 已终止（需要重启会话）
        """
        # 1. 检查终端窗口是否存活
        if not session.verify_alive():
            return "terminated"

        # 2. 使用终端原生的活跃检测（仅 Kitty 支持）
        if session.terminal:
            is_active = await session.terminal.is_cli_active()
            if is_active is not None:
                return "healthy" if is_active else "idle"

        # 其他终端不支持 idle 检测，只检测 terminated
        return "healthy"

    async def _get_template_by_task_status(self, task_id: str) -> str:
        """
        根据任务状态选择对应的模板

        Args:
            task_id: 任务ID

        Returns:
            模板名称
        """
        if not self._task_service:
            print(f"⚠️ TaskService 未注入，使用默认模板 continue_task")
            return "continue_task"

        try:
            # 查询任务状态
            task_data = await self._task_service.get_task_raw(task_id)
            if not task_data:
                print(f"⚠️ 任务 {task_id} 不存在，使用默认模板 continue_task")
                return "continue_task"

            task_status = task_data.get('status', '')

            # 根据状态映射模板
            if task_status == 'in_progress':
                return "resume_task"
            elif task_status == 'in_reviewing':
                return "review"
            else:
                # 其他状态（pending/completed/failed）使用 continue_task
                return "continue_task"

        except Exception as e:
            print(f"⚠️ 查询任务状态失败: {e}，使用默认模板 continue_task")
            return "continue_task"

    async def _handle_idle(self, task_id: str, session: "ManagedSession"):
        """处理心跳超时的会话 - 发送恢复消息唤醒 CLI"""
        print(f"😴 检测到会话 {task_id} 心跳超时，发送恢复消息...")

        try:
            # 渲染 continue_task 模板
            template_service = self._session_manager.template_service
            message = await template_service.render_template(
                template_type="continue_task",
                task_id=task_id,
                project_dir=session.project_dir,
                doc_path=session.doc_path,
                api_base_url=session.api_base_url
            )

            # 发送消息
            success = await self._session_manager.send_message(task_id, message)

            if success:
                # 更新活动时间，避免立即重复发送
                self.record_activity(task_id)
                print(f"✅ 已向会话 {task_id} 发送恢复消息")
            else:
                print(f"❌ 向会话 {task_id} 发送恢复消息失败")

        except Exception as e:
            print(f"❌ 处理 idle 会话异常: {e}")

    async def _handle_terminated(self, task_id: str, session: "ManagedSession"):
        """处理已终止的会话"""
        print(f"💀 检测到会话 {task_id} 意外终止，准备自动恢复...")

        # 触发回调（通知前端）
        if self._on_timeout:
            try:
                await self._on_timeout(task_id, "terminated")
            except Exception as e:
                print(f"⚠️ 超时回调执行失败: {e}")

        # 自动重启会话
        await self._auto_restart(task_id, session)

    async def _auto_restart(self, task_id: str, session: "ManagedSession"):
        """自动重启会话"""
        try:
            # 根据任务状态选择模板
            template_name = await self._get_template_by_task_status(task_id)
            print(f"🔄 根据任务状态选择模板: {template_name}")

            success = await self._session_manager.start_session(
                task_id=task_id,
                project_dir=session.project_dir,
                doc_path=session.doc_path,
                cli_type=session.cli_type,
                api_base_url=session.api_base_url,
                template_name=template_name
            )

            if success:
                self.record_activity(task_id)
                print(f"✅ 会话 {task_id} 已自动恢复（模板: {template_name}）")
            else:
                print(f"❌ 会话 {task_id} 自动恢复失败")

        except Exception as e:
            print(f"❌ 自动重启异常: {e}")
