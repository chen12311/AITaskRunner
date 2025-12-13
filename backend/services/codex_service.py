"""
CLI 服务 - 支持多种 AI CLI 工具（Claude Code、Codex、Gemini）
支持多项目并行运行
"""
import sys
from pathlib import Path

# 添加父目录到Python路径
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from core.session import SessionManager, ManagedSession, SessionStatus, SessionWatchdog
from backend.models.schemas import CodexStatusModel
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.services.settings_service import SettingsService


class CodexService:
    """CLI 服务 - 管理 AI CLI 会话和监控

    支持多项目并行运行，每个任务拥有独立的会话实例。
    使用 SessionManager 管理会话池。
    """

    def __init__(
        self,
        settings_service: "SettingsService" = None,
        task_service=None,
        max_concurrent_sessions: int = 3,
        db_path: str = None
    ):
        """
        初始化 CLI 服务

        Args:
            settings_service: 设置服务实例
            task_service: 任务服务实例（用于看门狗查询任务状态）
            max_concurrent_sessions: 最大并发会话数
            db_path: 数据库路径
        """
        self.settings_service = settings_service
        self.task_service = task_service
        self._db_path = db_path or str(parent_dir / "aitaskrunner.db")

        # 使用 SessionManager 管理多个会话
        self.session_manager = SessionManager(
            max_concurrent=max_concurrent_sessions,
            settings_service=settings_service,
            db_path=self._db_path
        )

        # 会话看门狗
        self.watchdog: Optional[SessionWatchdog] = None

        # 向后兼容：保留 current_task_id，但不再是主要依赖
        self._current_task_id: Optional[str] = None

    async def initialize(self):
        """异步初始化"""
        # 从设置获取最大并发数
        if self.settings_service:
            max_concurrent = await self.settings_service.get_max_concurrent_sessions()
            if max_concurrent:
                await self.session_manager.update_max_concurrent(max_concurrent)

    async def start_watchdog(self, on_timeout=None):
        """启动会话看门狗"""
        if self.watchdog is None:
            # 从设置读取看门狗参数
            heartbeat_timeout = 300.0
            check_interval = 30.0
            if self.settings_service:
                heartbeat_timeout = await self.settings_service.get_watchdog_heartbeat_timeout()
                check_interval = await self.settings_service.get_watchdog_check_interval()

            self.watchdog = SessionWatchdog(
                session_manager=self.session_manager,
                task_service=self.task_service,
                heartbeat_timeout=heartbeat_timeout,
                check_interval=check_interval,
                on_timeout=on_timeout
            )
        await self.watchdog.start()

    async def stop_watchdog(self):
        """停止会话看门狗"""
        if self.watchdog:
            await self.watchdog.stop()

    async def update_terminal_adapter(self):
        """更新终端适配器（设置变更时调用）"""
        # 新架构中，每个会话有自己的终端适配器
        # 此方法保留用于向后兼容，但不执行任何操作
        pass

    async def update_cli_adapter(self, cli_type: str = None):
        """更新 CLI 适配器"""
        # 新架构中，每个会话有自己的 CLI 适配器
        # 此方法保留用于向后兼容，但不执行任何操作
        pass

    async def start_session(
        self,
        task_id: str,
        project_dir: str,
        doc_path: str,
        api_base_url: str = "http://127.0.0.1:8086",
        cli_type: str = None,
        template_name: str = "initial_task"
    ) -> bool:
        """
        启动 CLI 会话

        Args:
            task_id: 任务ID
            project_dir: 项目目录
            doc_path: 文档路径
            api_base_url: API基础URL
            cli_type: CLI 类型 (claude_code, codex, gemini)
            template_name: 初始消息模板（默认 initial_task，Review 用 review）

        Returns:
            是否成功启动
        """
        try:
            success = await self.session_manager.start_session(
                task_id=task_id,
                project_dir=project_dir,
                doc_path=doc_path,
                cli_type=cli_type,
                api_base_url=api_base_url,
                template_name=template_name
            )

            if success:
                # 向后兼容：更新 current_task_id
                self._current_task_id = task_id
                # 记录心跳（看门狗用于检测会话存活）
                if self.watchdog:
                    self.watchdog.record_activity(task_id)

            return success

        except Exception as e:
            print(f"启动会话失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def stop_session(self, task_id: str = None):
        """
        停止 CLI 会话

        Args:
            task_id: 任务ID，如果为 None 则停止当前任务（向后兼容）
        """
        # 向后兼容：如果没有指定 task_id，使用当前任务
        if task_id is None:
            task_id = self._current_task_id

        if task_id is None:
            print("⚠️ 没有指定要停止的任务")
            return

        await self.session_manager.stop_session(task_id)

        # 清除看门狗心跳记录
        if self.watchdog:
            self.watchdog.clear_activity(task_id)

        # 向后兼容：如果停止的是当前任务，清除 current_task_id
        if task_id == self._current_task_id:
            self._current_task_id = None

    async def stop_all_sessions(self):
        """停止所有会话"""
        await self.session_manager.stop_all_sessions()
        self._current_task_id = None

    async def get_status(self, task_id: str = None) -> CodexStatusModel:
        """
        获取 CLI 状态

        Args:
            task_id: 任务ID，如果为 None 则获取当前任务状态（向后兼容）

        Returns:
            CodexStatusModel 状态对象
        """
        # 向后兼容：如果没有指定 task_id，使用当前任务
        if task_id is None:
            task_id = self._current_task_id

        if task_id is None:
            return CodexStatusModel(
                is_running=False,
                session_id=None,
                context_tokens=0,
                max_tokens=200000,
                context_usage=0.0,
                current_task_id=None
            )

        session = await self.session_manager.get_session(task_id)
        if session is None:
            return CodexStatusModel(
                is_running=False,
                session_id=None,
                context_tokens=0,
                max_tokens=200000,
                context_usage=0.0,
                current_task_id=task_id
            )

        return CodexStatusModel(
            is_running=session.status == SessionStatus.RUNNING,
            session_id=task_id,
            context_tokens=0,  # 可以从 CLI 适配器获取
            max_tokens=200000,
            context_usage=0.0,
            current_task_id=task_id
        )

    async def get_session_status(self, task_id: str) -> Optional[dict]:
        """
        获取指定会话的状态

        Args:
            task_id: 任务ID

        Returns:
            会话状态字典或 None
        """
        session = await self.session_manager.get_session(task_id)
        if session is None:
            return None
        return session.to_dict()

    def get_all_sessions(self) -> List[dict]:
        """
        获取所有会话状态

        Returns:
            所有会话状态列表
        """
        sessions = self.session_manager.get_all_sessions()
        return [s.to_dict() for s in sessions]

    def get_active_sessions(self) -> List[dict]:
        """
        获取所有活跃会话

        Returns:
            活跃会话状态列表
        """
        sessions = self.session_manager.get_active_sessions()
        return [s.to_dict() for s in sessions]

    def get_session_count(self) -> int:
        """获取当前会话总数"""
        return self.session_manager.get_session_count()

    def get_active_count(self) -> int:
        """获取活跃会话数"""
        return self.session_manager.get_active_count()

    def get_available_slots(self) -> int:
        """获取可用槽位数"""
        return self.session_manager.get_available_slots()

    async def send_message(self, message: str, task_id: str = None):
        """
        发送消息给 CLI

        Args:
            message: 消息内容
            task_id: 任务ID，如果为 None 则发送给当前任务（向后兼容）
        """
        # 向后兼容：如果没有指定 task_id，使用当前任务
        if task_id is None:
            task_id = self._current_task_id

        if task_id is None:
            print("❌ 没有指定要发送消息的任务")
            return

        await self.session_manager.send_message(task_id, message)

    async def restart_session(self, task_id: str = None):
        """
        重启会话

        Args:
            task_id: 任务ID，如果为 None 则重启当前任务（向后兼容）
        """
        # 向后兼容：如果没有指定 task_id，使用当前任务
        if task_id is None:
            task_id = self._current_task_id

        if task_id is None:
            print("❌ 没有指定要重启的任务")
            return

        await self.session_manager.restart_session(task_id)

    async def remove_session(self, task_id: str) -> bool:
        """
        移除会话（会先停止）

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        result = await self.session_manager.remove_session(task_id)

        # 清除看门狗心跳记录
        if self.watchdog:
            self.watchdog.clear_activity(task_id)

        # 向后兼容：如果移除的是当前任务，清除 current_task_id
        if task_id == self._current_task_id:
            self._current_task_id = None

        return result

    # ===== 向后兼容属性 =====

    @property
    def current_task_id(self) -> Optional[str]:
        """当前任务ID（向后兼容）"""
        return self._current_task_id

    @property
    def monitor(self):
        """获取当前任务的 monitor（向后兼容）

        注意：新代码应使用 session_manager.get_session(task_id) 获取会话
        """
        if self._current_task_id:
            # 由于是同步属性，无法使用 await
            # 返回 None，调用者应使用新的异步方法
            return None
        return None
