"""
会话管理器 - 管理多个并发的 CLI 会话
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

from core.session.models import ManagedSession, SessionStatus
from core.terminal_adapters import (
    TerminalAdapter,
    KittyAdapter,
    iTermAdapter,
    WindowsTerminalAdapter,
    get_default_terminal_adapter
)
from core.cli_adapters import get_cli_adapter

if TYPE_CHECKING:
    from backend.services.settings_service import SettingsService
    from backend.services.template_service import TemplateService


class SessionManager:
    """
    会话管理器 - 管理多个并发的 CLI 会话

    使用 semaphore 控制最大并发数，使用 lock 保护并发操作。
    所有操作都有超时保护，避免永久阻塞。
    """

    # 默认超时时间（秒）
    DEFAULT_LOCK_TIMEOUT = 10.0  # 锁超时
    DEFAULT_SEMAPHORE_TIMEOUT = 30.0  # 信号量超时
    DEFAULT_TERMINAL_TIMEOUT = 15.0  # 终端操作超时
    DEFAULT_CLEANUP_TIMEOUT = 5.0  # 清理超时

    def __init__(
        self,
        max_concurrent: int = 3,
        settings_service: "SettingsService" = None,
        template_service: "TemplateService" = None,
        db_path: str = None
    ):
        """
        初始化会话管理器

        Args:
            max_concurrent: 最大并发会话数
            settings_service: 设置服务实例
            template_service: 模板服务实例
            db_path: 数据库路径
        """
        self.max_concurrent = max_concurrent
        self._settings_service = settings_service
        self._template_service = template_service
        self._db_path = db_path

        # 会话字典：task_id -> ManagedSession
        self._sessions: Dict[str, ManagedSession] = {}

        # 并发控制
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()

    async def _acquire_lock(self, timeout: float = None) -> bool:
        """获取锁（带超时）"""
        timeout = timeout or self.DEFAULT_LOCK_TIMEOUT
        try:
            return await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"⚠️ 获取锁超时 ({timeout}秒)")
            return False

    async def _acquire_semaphore(self, timeout: float = None) -> bool:
        """获取信号量（带超时）"""
        timeout = timeout or self.DEFAULT_SEMAPHORE_TIMEOUT
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            print(f"⚠️ 获取信号量超时 ({timeout}秒)")
            return False

    @property
    def template_service(self) -> "TemplateService":
        """延迟加载模板服务"""
        if self._template_service is None:
            from backend.services.template_service import TemplateService
            self._template_service = TemplateService(self._db_path)
        return self._template_service

    @property
    def settings_service(self) -> "SettingsService":
        """延迟加载设置服务"""
        if self._settings_service is None:
            from backend.services.settings_service import SettingsService
            self._settings_service = SettingsService(self._db_path)
        return self._settings_service

    async def _get_terminal_type(self) -> str:
        """获取配置的终端类型"""
        if self._settings_service:
            return await self._settings_service.get_terminal_type()
        return "auto"

    async def _get_cli_type(self) -> str:
        """获取配置的 CLI 类型"""
        if self._settings_service:
            return await self._settings_service.get_cli_type()
        return "claude_code"

    async def _create_terminal_adapter(self) -> Optional[TerminalAdapter]:
        """创建新的终端适配器实例"""
        terminal_type = await self._get_terminal_type()

        adapter = None
        if terminal_type == "kitty":
            adapter = KittyAdapter()
        elif terminal_type == "iterm":
            adapter = iTermAdapter()
        elif terminal_type == "windows_terminal":
            adapter = WindowsTerminalAdapter()
        elif terminal_type == "auto":
            adapter = get_default_terminal_adapter()
        else:
            print(f"❌ 不支持的终端类型: {terminal_type}")
            return None

        if adapter and adapter.is_available():
            return adapter
        else:
            print(f"❌ 终端适配器不可用")
            return None

    def _create_cli_adapter(self, cli_type: str):
        """创建新的 CLI 适配器实例"""
        try:
            adapter = get_cli_adapter(cli_type)
            if adapter.is_available():
                return adapter
            else:
                print(f"❌ {adapter.name} 未安装")
                return None
        except ValueError as e:
            print(f"❌ {e}")
            return None

    async def create_session(
        self,
        task_id: str,
        project_dir: str,
        doc_path: str,
        cli_type: str = None,
        api_base_url: str = "http://127.0.0.1:8086"
    ) -> Optional[ManagedSession]:
        """
        创建新的会话

        Args:
            task_id: 任务ID
            project_dir: 项目目录
            doc_path: 文档路径
            cli_type: CLI 类型
            api_base_url: API 基础 URL

        Returns:
            创建的 ManagedSession，失败返回 None
        """
        # 检查是否已存在（带超时锁）
        if not await self._acquire_lock():
            print(f"❌ 创建会话 {task_id} 时获取锁超时")
            return None

        try:
            if task_id in self._sessions:
                existing = self._sessions[task_id]
                if existing.is_active():
                    print(f"⚠️ 任务 {task_id} 已有活跃会话")
                    return existing
                else:
                    # 清理旧会话
                    await self._cleanup_session(existing)
                    if existing.semaphore_acquired:
                        self._semaphore.release()
                        existing.semaphore_acquired = False
                    del self._sessions[task_id]
        finally:
            self._lock.release()

        # 尝试获取 semaphore（非阻塞检查）
        if self._semaphore._value <= 0:
            print(f"❌ 已达最大并发数 {self.max_concurrent}，无法创建新会话")
            return None

        # 获取 semaphore（带超时）
        if not await self._acquire_semaphore():
            print(f"❌ 创建会话 {task_id} 时获取信号量超时")
            return None

        try:
            # 获取 CLI 类型
            if not cli_type:
                cli_type = await self._get_cli_type()

            # 创建终端和 CLI 适配器
            terminal = await self._create_terminal_adapter()
            if not terminal:
                self._semaphore.release()
                return None

            cli_adapter = self._create_cli_adapter(cli_type)
            if not cli_adapter:
                self._semaphore.release()
                return None

            # 创建 ManagedSession（不再需要 CLIMonitor）
            session = ManagedSession(
                task_id=task_id,
                monitor=None,  # 不再使用单独的 monitor
                terminal=terminal,
                cli_adapter=cli_adapter,
                status=SessionStatus.IDLE,
                project_dir=project_dir,
                doc_path=doc_path,
                cli_type=cli_type,
                api_base_url=api_base_url,
                created_at=datetime.now()
            )
            session.semaphore_acquired = True

            # 注册会话（带超时锁）
            if not await self._acquire_lock():
                self._semaphore.release()
                print(f"❌ 注册会话 {task_id} 时获取锁超时")
                return None

            try:
                self._sessions[task_id] = session
            finally:
                self._lock.release()

            print(f"✅ 创建会话: {task_id} ({cli_type}, {terminal.name})")
            return session

        except Exception as e:
            self._semaphore.release()
            print(f"❌ 创建会话失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def start_session(
        self,
        task_id: str,
        project_dir: str = None,
        doc_path: str = None,
        cli_type: str = None,
        api_base_url: str = "http://127.0.0.1:8086",
        template_name: str = "initial_task"
    ) -> bool:
        """
        启动会话

        如果会话不存在，先创建；然后启动 CLI。

        Args:
            task_id: 任务ID
            project_dir: 项目目录（创建新会话时必需）
            template_name: 初始消息模板名称（默认 initial_task，Review 用 review）
            doc_path: 文档路径（创建新会话时必需）
            cli_type: CLI 类型
            api_base_url: API 基础 URL

        Returns:
            是否成功启动
        """
        session = await self.get_session(task_id)

        # 如果会话不存在，创建新会话
        if not session:
            if not project_dir or not doc_path:
                print(f"❌ 创建新会话需要 project_dir 和 doc_path")
                return False

            session = await self.create_session(
                task_id=task_id,
                project_dir=project_dir,
                doc_path=doc_path,
                cli_type=cli_type,
                api_base_url=api_base_url
            )
            if not session:
                return False
        else:
            # 更新会话参数
            if project_dir:
                session.project_dir = project_dir
            if doc_path:
                session.doc_path = doc_path
            if api_base_url:
                session.api_base_url = api_base_url
            # 更新 CLI 类型（Review 阶段需要切换 CLI）
            if cli_type and cli_type != session.cli_type:
                new_adapter = self._create_cli_adapter(cli_type)
                if new_adapter:
                    old_cli_type = session.cli_type
                    session.cli_adapter = new_adapter
                    session.cli_type = cli_type
                    print(f"🔄 会话 {task_id} CLI 切换: {old_cli_type} → {cli_type}")

        # 如果会话已停止但仍持有 semaphore，先释放占用槽位
        if session.is_terminal() and session.semaphore_acquired:
            self._semaphore.release()
            session.semaphore_acquired = False

        # 检查状态（使用 verify_alive 检测幽灵会话）
        if session.verify_alive():
            print(f"⚠️ 会话 {task_id} 已在运行中")
            return True

        # 未持有 semaphore 时尝试获取新槽位（带超时）
        if not session.semaphore_acquired:
            if self._semaphore._value <= 0:
                print(f"❌ 已达最大并发数 {self.max_concurrent}，无法启动会话")
                return False
            if not await self._acquire_semaphore():
                print(f"❌ 启动会话 {task_id} 时获取信号量超时")
                return False
            session.semaphore_acquired = True

        try:
            session.mark_starting()

            # 读取初始任务内容（使用指定的模板和语言设置，带超时）
            try:
                locale = await asyncio.wait_for(
                    self.settings_service.get_language(),
                    timeout=self.DEFAULT_LOCK_TIMEOUT
                )
                initial_message = await asyncio.wait_for(
                    self.template_service.render_template_async(
                        template_name,
                        locale=locale,
                        project_dir=session.project_dir,
                        doc_path=session.doc_path,
                        task_id=task_id,
                        api_base_url=session.api_base_url
                    ),
                    timeout=self.DEFAULT_LOCK_TIMEOUT
                )
            except asyncio.TimeoutError:
                session.mark_error("获取模板超时")
                if session.semaphore_acquired:
                    self._semaphore.release()
                    session.semaphore_acquired = False
                return False

            # 获取启动命令
            command = session.cli_adapter.get_start_command(session.project_dir)

            # 创建终端窗口（带超时）
            try:
                terminal_session = await asyncio.wait_for(
                    session.terminal.create_window(
                        project_dir=session.project_dir,
                        command=command,
                        task_id=task_id,
                        api_base_url=session.api_base_url
                    ),
                    timeout=self.DEFAULT_TERMINAL_TIMEOUT
                )
            except asyncio.TimeoutError:
                session.mark_error("创建终端窗口超时")
                if session.semaphore_acquired:
                    self._semaphore.release()
                    session.semaphore_acquired = False
                return False

            if not terminal_session:
                session.mark_error("创建终端窗口失败")
                if session.semaphore_acquired:
                    self._semaphore.release()
                    session.semaphore_acquired = False
                return False

            # 等待 CLI 启动
            await asyncio.sleep(1.5)

            # 发送初始消息（带超时）
            try:
                clear_cmd = session.cli_adapter.get_clear_session_command()
                if clear_cmd:
                    await asyncio.wait_for(
                        session.terminal.send_text(clear_cmd, press_enter=True),
                        timeout=self.DEFAULT_TERMINAL_TIMEOUT
                    )
                    await asyncio.sleep(0.5)

                formatted_prompt = session.cli_adapter.format_initial_prompt(initial_message)
                await asyncio.wait_for(
                    session.terminal.send_text(formatted_prompt, press_enter=True),
                    timeout=self.DEFAULT_TERMINAL_TIMEOUT
                )
            except asyncio.TimeoutError:
                session.mark_error("发送初始消息超时")
                if session.semaphore_acquired:
                    self._semaphore.release()
                    session.semaphore_acquired = False
                return False

            session.mark_running()
            print(f"✅ 会话 {task_id} 已启动")
            return True

        except Exception as e:
            session.mark_error(str(e))
            if session.semaphore_acquired:
                self._semaphore.release()
                session.semaphore_acquired = False
            print(f"❌ 启动会话失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def get_session(self, task_id: str) -> Optional[ManagedSession]:
        """
        获取指定任务的会话

        Args:
            task_id: 任务ID

        Returns:
            ManagedSession 或 None
        """
        if not await self._acquire_lock():
            print(f"⚠️ 获取会话 {task_id} 时获取锁超时")
            return None
        try:
            return self._sessions.get(task_id)
        finally:
            self._lock.release()

    async def remove_session(self, task_id: str) -> bool:
        """
        移除会话（会先停止）

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        if not await self._acquire_lock():
            print(f"⚠️ 移除会话 {task_id} 时获取锁超时")
            return False

        try:
            session = self._sessions.get(task_id)
            if not session:
                return False

            # 清理会话
            await self._cleanup_session(session)

            # 从字典中移除
            del self._sessions[task_id]

            # 释放 semaphore
            if session.semaphore_acquired:
                self._semaphore.release()
                session.semaphore_acquired = False

            print(f"✅ 已移除会话: {task_id}")
            return True
        finally:
            self._lock.release()

    async def stop_session(self, task_id: str, timeout: float = 5.0) -> bool:
        """
        停止会话（不移除，可重启）

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            是否成功
        """
        session = await self.get_session(task_id)
        if not session:
            print(f"⚠️ 会话 {task_id} 不存在")
            return False

        # 即使会话已标记为终止状态，仍需尝试关闭终端窗口
        # 因为状态可能已更新，但窗口可能仍然打开
        if session.is_terminal():
            if session.semaphore_acquired:
                self._semaphore.release()
                session.semaphore_acquired = False
            # 尝试关闭终端窗口（即使状态已终止）
            if session.terminal and session.terminal.has_active_session():
                try:
                    await asyncio.wait_for(
                        session.terminal.close_window(),
                        timeout=timeout
                    )
                    print(f"✅ 已关闭会话 {task_id} 的终端窗口")
                except asyncio.TimeoutError:
                    print(f"⚠️ 关闭终端窗口超时: {task_id}")
            else:
                print(f"⚠️ 会话 {task_id} 已停止")
            return True

        try:
            session.mark_stopping()

            # 取消监控任务（带超时）
            if session.monitor_task and not session.monitor_task.done():
                session.monitor_task.cancel()
                try:
                    await asyncio.wait_for(
                        asyncio.shield(session.monitor_task),
                        timeout=timeout
                    )
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            # 关闭终端窗口（带超时）
            if session.terminal:
                try:
                    await asyncio.wait_for(
                        session.terminal.close_window(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    print(f"⚠️ 关闭终端窗口超时: {task_id}")

            session.mark_stopped()
            if session.semaphore_acquired:
                self._semaphore.release()
                session.semaphore_acquired = False
            print(f"✅ 会话 {task_id} 已停止")
            return True

        except Exception as e:
            if session.semaphore_acquired:
                self._semaphore.release()
                session.semaphore_acquired = False
            session.mark_error(str(e))
            print(f"❌ 停止会话失败: {e}")
            return False

    async def stop_all_sessions(self) -> None:
        """停止所有会话"""
        if not await self._acquire_lock():
            print(f"⚠️ 停止所有会话时获取锁超时")
            return

        try:
            task_ids = list(self._sessions.keys())
        finally:
            self._lock.release()

        for task_id in task_ids:
            await self.stop_session(task_id)

        print(f"✅ 已停止所有 {len(task_ids)} 个会话")

    def get_active_sessions(self) -> List[ManagedSession]:
        """获取所有活跃会话"""
        return [s for s in self._sessions.values() if s.is_active()]

    def get_all_sessions(self) -> List[ManagedSession]:
        """获取所有会话"""
        return list(self._sessions.values())

    def get_session_count(self) -> int:
        """获取当前会话总数"""
        return len(self._sessions)

    def get_active_count(self) -> int:
        """获取活跃会话数"""
        return len(self.get_active_sessions())

    def get_available_slots(self) -> int:
        """获取可用槽位数"""
        return self.max_concurrent - self.get_active_count()

    async def send_message(self, task_id: str, message: str, press_enter: bool = True) -> bool:
        """
        向指定会话发送消息

        Args:
            task_id: 任务ID
            message: 消息内容
            press_enter: 是否按回车发送

        Returns:
            是否成功
        """
        session = await self.get_session(task_id)
        if not session:
            print(f"❌ 会话 {task_id} 不存在")
            return False

        if not session.is_active():
            print(f"❌ 会话 {task_id} 未在运行")
            return False

        try:
            # 发送消息（带超时）
            success = await asyncio.wait_for(
                session.terminal.send_text(message, press_enter=press_enter),
                timeout=self.DEFAULT_TERMINAL_TIMEOUT
            )
            if success:
                print(f"✅ 已向会话 {task_id} 发送消息")
            else:
                print(f"❌ 向会话 {task_id} 发送消息失败")
            return success
        except asyncio.TimeoutError:
            print(f"❌ 向会话 {task_id} 发送消息超时")
            return False
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return False

    async def restart_session(self, task_id: str) -> bool:
        """
        重启会话

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        session = await self.get_session(task_id)
        if not session:
            print(f"❌ 会话 {task_id} 不存在")
            return False

        # 保存会话参数
        project_dir = session.project_dir
        doc_path = session.doc_path
        api_base_url = session.api_base_url

        # 停止会话
        await self.stop_session(task_id)

        # 重新启动
        success = await self.start_session(
            task_id=task_id,
            project_dir=project_dir,
            doc_path=doc_path,
            api_base_url=api_base_url
        )

        if success:
            # 发送恢复消息
            resume_message = await self.template_service.render_template_async(
                'resume_task',
                project_dir=project_dir,
                doc_path=doc_path,
                task_id=task_id,
                api_base_url=api_base_url
            )
            await self.send_message(task_id, resume_message)

        return success

    async def _cleanup_session(self, session: ManagedSession, timeout: float = 5.0):
        """清理会话资源（带超时保护）"""
        try:
            # 取消监控任务（带超时）
            if session.monitor_task and not session.monitor_task.done():
                session.monitor_task.cancel()
                try:
                    await asyncio.wait_for(
                        asyncio.shield(session.monitor_task),
                        timeout=timeout
                    )
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            # 关闭终端窗口（带超时）
            if session.terminal and session.terminal.has_active_session():
                try:
                    await asyncio.wait_for(
                        session.terminal.close_window(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    print(f"⚠️ 清理会话时关闭终端超时: {session.task_id}")

            session.mark_stopped()

        except Exception as e:
            print(f"⚠️ 清理会话 {session.task_id} 失败: {e}")

    async def update_max_concurrent(self, max_concurrent: int):
        """
        更新最大并发数

        注意：只会影响新会话的创建，不会影响已有会话

        Args:
            max_concurrent: 新的最大并发数
        """
        if max_concurrent < 1:
            print(f"⚠️ 最大并发数必须 >= 1")
            return

        old_value = self.max_concurrent
        self.max_concurrent = max_concurrent

        # 重新创建 semaphore（保留已使用的槽位）
        current_active = self.get_active_count()
        available = max(0, max_concurrent - current_active)
        self._semaphore = asyncio.Semaphore(available)

        print(f"✅ 最大并发数从 {old_value} 更新为 {max_concurrent}")
