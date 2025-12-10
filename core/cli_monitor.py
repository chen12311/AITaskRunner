"""
CLI 监控器 - 监控 AI CLI 工具运行状态和上下文使用
支持 Claude Code、OpenAI Codex CLI、Google Gemini CLI
支持多种终端（Kitty、iTerm、Windows Terminal）
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional, TYPE_CHECKING

# 添加父目录到路径以导入 backend 模块
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from core.terminal_adapters import (
    TerminalAdapter,
    KittyAdapter,
    iTermAdapter,
    WindowsTerminalAdapter,
    get_default_terminal_adapter
)
from core.cli_adapters import CLIAdapter, CLIStatus, CLIType, get_cli_adapter

if TYPE_CHECKING:
    from backend.services.settings_service import SettingsService
    from core.terminal_adapters.base import TerminalAdapter as TerminalAdapterType
    from core.cli_adapters.base import CLIAdapter as CLIAdapterType


class CLIMonitor:
    """CLI 监控器 - 支持多终端和多 CLI 工具

    支持多实例化，每个实例可以独立管理一个会话。
    """

    def __init__(
        self,
        context_threshold: float = 0.8,
        db_path: str = None,
        settings_service: "SettingsService" = None,
        cli_type: str = "claude_code",
        task_id: str = None,
        terminal_adapter: "TerminalAdapter" = None,
        cli_adapter: "CLIAdapter" = None
    ):
        """
        初始化 CLI 监控器

        Args:
            context_threshold: 上下文使用阈值，超过则触发重启
            db_path: 数据库路径
            settings_service: 设置服务实例
            cli_type: CLI 类型 ("claude_code", "codex", "gemini")
            task_id: 任务ID，用于标识所属任务（多实例场景）
            terminal_adapter: 外部传入的终端适配器（可选，用于多实例场景）
            cli_adapter: 外部传入的 CLI 适配器（可选，用于多实例场景）
        """
        self.context_threshold = context_threshold
        self.session_active = False
        self.current_project_dir: Optional[str] = None
        self.current_doc_path: Optional[str] = None
        self.current_task_id: Optional[str] = task_id
        self.current_api_base_url: Optional[str] = None

        # 设置服务
        self._settings_service = settings_service

        # CLI 适配器（支持外部传入）
        self._cli_type = cli_type
        self._cli_adapter: Optional[CLIAdapter] = cli_adapter

        # 终端适配器（支持外部传入）
        self._terminal: Optional[TerminalAdapter] = terminal_adapter

        # 模板服务（延迟初始化）
        self._template_service = None
        self._db_path = db_path or str(parent_dir / "aitaskrunner.db")

    async def initialize(self):
        """异步初始化

        只在没有外部传入适配器时才创建新实例。
        """
        # 初始化 CLI 适配器（如果未外部传入）
        if self._cli_adapter is None:
            cli_type = await self._get_cli_type()
            self._init_cli_adapter(cli_type)

        # 初始化终端适配器（如果未外部传入）
        if self._terminal is None:
            await self._init_terminal_adapter()

    def _init_cli_adapter(self, cli_type: str):
        """初始化 CLI 适配器"""
        try:
            self._cli_adapter = get_cli_adapter(cli_type)
            if self._cli_adapter.is_available():
                print(f"✅ 使用 {self._cli_adapter.name}")
            else:
                print(f"❌ {self._cli_adapter.name} 未安装")
                self._cli_adapter = None
        except ValueError as e:
            print(f"❌ {e}")
            self._cli_adapter = None

    async def _init_terminal_adapter(self):
        """初始化终端适配器"""
        terminal_type = await self._get_terminal_type()

        if terminal_type == "kitty":
            adapter = KittyAdapter()
            if adapter.is_available():
                self._terminal = adapter
                print(f"✅ 使用 Kitty 终端（支持后台操作）")
            else:
                print(f"❌ Kitty 未安装，请先安装 Kitty")
                self._terminal = None

        elif terminal_type == "iterm":
            adapter = iTermAdapter()
            if adapter.is_available():
                self._terminal = adapter
                print(f"✅ 使用 iTerm 终端（需要短暂切换焦点）")
            else:
                print(f"❌ iTerm 未安装，请先安装 iTerm")
                self._terminal = None

        elif terminal_type == "windows_terminal":
            adapter = WindowsTerminalAdapter()
            if adapter.is_available():
                self._terminal = adapter
                print(f"✅ 使用 Windows Terminal（需要短暂切换焦点）")
            else:
                print(f"❌ Windows Terminal 未安装，请先安装 Windows Terminal")
                self._terminal = None

        elif terminal_type == "auto":
            # 自动检测并使用默认终端
            adapter = get_default_terminal_adapter()
            if adapter:
                self._terminal = adapter
                print(f"✅ 自动检测到 {adapter.name}")
            else:
                print(f"❌ 未检测到可用的终端")
                self._terminal = None

        else:
            print(f"❌ 不支持的终端类型: {terminal_type}")
            self._terminal = None

    async def _get_terminal_type(self) -> str:
        """获取配置的终端类型"""
        if self._settings_service:
            return await self._settings_service.get_terminal_type()
        return "auto"  # 默认自动检测

    async def _get_cli_type(self) -> str:
        """获取配置的 CLI 类型"""
        if self._settings_service:
            return await self._settings_service.get_cli_type()
        return self._cli_type

    async def update_terminal_adapter(self):
        """更新终端适配器（设置变更时调用）"""
        await self._init_terminal_adapter()

    async def update_cli_adapter(self, cli_type: str = None):
        """更新 CLI 适配器"""
        if cli_type:
            self._cli_type = cli_type
        else:
            self._cli_type = await self._get_cli_type()
        self._init_cli_adapter(self._cli_type)

    @property
    def cli_adapter(self) -> Optional[CLIAdapter]:
        """获取当前 CLI 适配器"""
        return self._cli_adapter

    @property
    def cli_type(self) -> str:
        """获取当前 CLI 类型"""
        return self._cli_type

    @property
    def template_service(self):
        """延迟加载模板服务"""
        if self._template_service is None:
            from backend.services.template_service import TemplateService
            self._template_service = TemplateService(self._db_path)
        return self._template_service

    async def start_session(
        self,
        project_dir: str,
        doc_path: str,
        task_id: str = None,
        api_base_url: str = "http://127.0.0.1:8086",
        cli_type: str = None
    ) -> bool:
        """
        启动 CLI 会话

        Args:
            project_dir: 项目目录路径
            doc_path: 任务文档路径
            task_id: 任务ID
            api_base_url: API基础URL
            cli_type: CLI 类型（可选，覆盖默认）

        Returns:
            是否成功启动
        """
        # 如果指定了不同的 CLI 类型，切换适配器
        if cli_type and cli_type != self._cli_type:
            await self.update_cli_adapter(cli_type)

        if not self._cli_adapter:
            print(f"❌ 没有可用的 CLI 适配器")
            return False

        if not self._terminal:
            print(f"❌ 没有可用的终端适配器")
            return False

        try:
            print(f"🚀 启动 {self._cli_adapter.name} 会话")
            print(f"   终端: {self._terminal.name}")
            print(f"   项目目录: {project_dir}")
            print(f"   任务文档: {doc_path}")
            if task_id:
                print(f"   任务ID: {task_id}")

            # 读取初始任务内容
            initial_message = await self.template_service.render_template_async(
                'initial_task',
                project_dir=project_dir,
                doc_path=doc_path,
                task_id=task_id,
                api_base_url=api_base_url
            )

            # 获取启动命令
            command = self._cli_adapter.get_start_command(project_dir)

            # 使用终端适配器创建窗口
            session = await self._terminal.create_window(
                project_dir=project_dir,
                command=command,
                task_id=task_id,
                api_base_url=api_base_url
            )

            if not session:
                print(f"❌ 创建终端窗口失败")
                return False

            # 等待 CLI 完全启动
            await asyncio.sleep(1.5)

            self.session_active = True
            self.current_project_dir = project_dir
            self.current_doc_path = doc_path
            self.current_task_id = task_id
            self.current_api_base_url = api_base_url

            print(f"✅ 已在 {self._terminal.name} 中启动 {self._cli_adapter.name} 会话")

            # 发送初始任务消息
            print(f"📤 发送初始任务...")

            # 如果 CLI 支持清空会话，先清空
            clear_cmd = self._cli_adapter.get_clear_session_command()
            if clear_cmd:
                await self.send_message(clear_cmd, press_enter=True)
                await asyncio.sleep(0.5)

            # 格式化并发送初始提示
            formatted_prompt = self._cli_adapter.format_initial_prompt(initial_message)
            await self.send_message(formatted_prompt, press_enter=True)

            return True

        except Exception as e:
            print(f"❌ 启动会话失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def send_initial_task(self, project_dir: str, doc_path: str):
        """发送初始任务 - 使用数据库模板"""
        message = await self.template_service.render_template_async(
            'initial_task',
            project_dir=project_dir,
            doc_path=doc_path
        )
        formatted = self._cli_adapter.format_initial_prompt(message) if self._cli_adapter else message
        await self.send_message(formatted)

    async def send_message(self, message: str, press_enter: bool = True):
        """
        发送消息给 CLI

        Args:
            message: 要发送的消息内容
            press_enter: 是否按回车发送
        """
        if not self.session_active:
            raise RuntimeError("CLI 会话未激活")

        if not self._terminal:
            raise RuntimeError("没有可用的终端适配器")

        success = await self._terminal.send_text(message, press_enter=press_enter)
        if success:
            print(f"✅ 已发送消息")
        else:
            print(f"❌ 发送消息失败")

    async def get_status(self) -> CLIStatus:
        """
        获取 CLI 运行状态

        Returns:
            CLIStatus 对象
        """
        if not self._cli_adapter:
            return CLIStatus(is_running=False)

        return await self._cli_adapter.get_status()

    async def should_restart_session(self) -> bool:
        """判断是否需要重启会话"""
        if not self._cli_adapter:
            return False

        # 如果 CLI 不支持状态查询，不自动重启
        if not self._cli_adapter.supports_status_check():
            return False

        status = await self.get_status()
        return status.context_usage >= self.context_threshold

    async def restart_session(self):
        """重启 CLI 会话"""
        if not self.current_project_dir or not self.current_doc_path:
            raise RuntimeError("没有当前任务信息")

        print(f"🔄 上下文使用率过高，重启会话...")

        # 1. 清理当前会话
        await self.cleanup_session()

        # 2. 重新启动会话
        await self.start_session(
            self.current_project_dir,
            self.current_doc_path,
            self.current_task_id,
            self.current_api_base_url
        )

        # 3. 发送恢复任务消息
        await self.send_resume_message()

    async def send_resume_message(self):
        """发送恢复任务消息 - 使用数据库模板"""
        message = await self.template_service.render_template_async(
            'resume_task',
            project_dir=self.current_project_dir,
            doc_path=self.current_doc_path,
            task_id=self.current_task_id,
            api_base_url=self.current_api_base_url
        )
        formatted = self._cli_adapter.format_initial_prompt(message) if self._cli_adapter else message
        await self.send_message(formatted)

    async def cleanup_session(self):
        """清理会话"""
        try:
            self.session_active = False
            self.current_task_id = None
            self.current_api_base_url = None

            # 关闭终端窗口
            if self._terminal:
                await self._terminal.close_window()

            cli_name = self._cli_adapter.name if self._cli_adapter else "CLI"
            print(f"✅ 已清理 {cli_name} 会话")

        except Exception as e:
            print(f"⚠️ 清理会话失败: {e}")

    async def monitor_loop(self):
        """主监控循环"""
        while self.session_active:
            try:
                # 检查是否需要重启
                if await self.should_restart_session():
                    await self.restart_session()

                # 等待10秒再检查
                await asyncio.sleep(10)

            except Exception as e:
                print(f"❌ 监控循环出错: {e}")
                await asyncio.sleep(30)


# 向后兼容别名
CodexMonitor = CLIMonitor
CodexStatus = CLIStatus
