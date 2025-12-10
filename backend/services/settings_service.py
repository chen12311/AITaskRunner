"""
系统设置服务 - 管理终端选择等配置 - 异步版本
"""
import os
import platform
from typing import Optional, Dict, Any
from pathlib import Path
from backend.database.models import Database, SettingsDAO


class SettingsService:
    """系统设置服务 - 异步版本"""

    # 默认设置
    DEFAULT_SETTINGS = {
        "terminal": "auto",  # 默认自动检测终端
        "default_cli": "claude_code",  # 默认 CLI 类型
        "review_enabled": "false",  # 是否启用审查功能
        "review_cli": "codex",  # Review 阶段使用的 CLI 类型
        "api_base_url": "http://127.0.0.1:8086",  # API 基础 URL
        "max_concurrent_sessions": "3",  # 最大并发会话数
        "language": "zh",  # 界面语言：zh 或 en
    }

    # 支持的终端类型（按平台）
    SUPPORTED_TERMINALS = {
        "Darwin": ["auto", "kitty", "iterm"],  # macOS
        "Linux": ["auto", "kitty"],
        "Windows": ["auto", "windows_terminal"],
    }

    def __init__(self, db_path: str = None, db: Database = None):
        """
        初始化设置服务

        优化6.2: 支持注入共享数据库实例

        Args:
            db_path: 数据库文件路径（如果 db 为 None 时使用）
            db: 共享的数据库实例（优先使用）
        """
        if db is not None:
            self.db = db
        else:
            if db_path is None:
                db_path = str(Path(__file__).parent.parent.parent / "aitaskrunner.db")
            self.db = Database(db_path)
        self.settings_dao = SettingsDAO(self.db)
        self._initialized = False

    async def initialize(self):
        """初始化数据库和默认设置"""
        if not self._initialized:
            await self.db.initialize()
            # 插入默认设置（如果不存在）
            for key, value in self.DEFAULT_SETTINGS.items():
                existing = await self.settings_dao.get_setting(key)
                if existing is None:
                    await self.settings_dao.set_setting(
                        key, value, self._get_setting_description(key)
                    )
            self._initialized = True

    def _get_setting_description(self, key: str) -> str:
        """获取设置项描述"""
        system = platform.system()
        supported = self.SUPPORTED_TERMINALS.get(system, ["auto"])
        terminal_desc = f"终端类型，支持: {', '.join(supported)}"

        descriptions = {
            "terminal": terminal_desc,
            "default_cli": "默认 CLI 类型：claude_code、codex 或 gemini",
            "review_enabled": "是否启用审查功能：true 或 false",
            "review_cli": "Review 阶段使用的 CLI 类型：claude_code、codex 或 gemini",
            "api_base_url": "API 基础 URL，用于回调通知",
            "max_concurrent_sessions": "最大并发会话数，默认 3",
            "language": "界面语言：zh (中文) 或 en (English)",
        }
        return descriptions.get(key, "")

    async def get_setting(self, key: str) -> Optional[str]:
        """获取单个设置"""
        # api_base_url 从环境变量读取
        if key == "api_base_url":
            return os.environ.get("API_BASE_URL", self.DEFAULT_SETTINGS.get("api_base_url"))

        await self.initialize()
        value = await self.settings_dao.get_setting(key)
        if value is not None:
            return value
        return self.DEFAULT_SETTINGS.get(key)

    async def set_setting(self, key: str, value: str) -> bool:
        """设置单个配置"""
        await self.initialize()
        try:
            return await self.settings_dao.set_setting(
                key, value, self._get_setting_description(key)
            )
        except Exception as e:
            print(f"❌ 设置保存失败: {e}")
            return False

    async def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        await self.initialize()
        settings_dict = await self.settings_dao.get_all_settings()

        # 格式化输出
        settings = {}
        for key, value in settings_dict.items():
            settings[key] = {
                "value": value,
                "description": self._get_setting_description(key),
            }

        # 补充默认值
        for key, default_value in self.DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = {
                    "value": default_value,
                    "description": self._get_setting_description(key),
                }

        return settings

    async def get_terminal_type(self) -> str:
        """获取当前终端类型"""
        value = await self.get_setting("terminal")
        return value or "auto"

    def get_terminal_type_sync(self) -> str:
        """获取当前终端类型（同步版本，用于非异步上下文）"""
        # 注意：这是临时方法，应该逐步迁移所有调用为异步
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在异步上下文中，无法使用同步方法
                return "auto"
            return loop.run_until_complete(self.get_terminal_type())
        except RuntimeError:
            return "auto"

    async def set_terminal_type(self, terminal: str) -> bool:
        """设置终端类型"""
        system = platform.system()
        supported = self.SUPPORTED_TERMINALS.get(system, ["auto"])
        if terminal not in supported:
            raise ValueError(f"不支持的终端类型: {terminal}，当前平台 ({system}) 支持: {', '.join(supported)}")
        return await self.set_setting("terminal", terminal)

    async def get_supported_terminals(self) -> list[str]:
        """获取当前平台支持的终端类型"""
        system = platform.system()
        return self.SUPPORTED_TERMINALS.get(system, ["auto"])

    async def get_cli_type(self) -> str:
        """获取默认 CLI 类型"""
        value = await self.get_setting("default_cli")
        return value or "claude_code"

    def get_cli_type_sync(self) -> str:
        """获取默认 CLI 类型（同步版本，用于非异步上下文）"""
        # 注意：这是临时方法，应该逐步迁移所有调用为异步
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在异步上下文中，无法使用同步方法
                return "claude_code"
            return loop.run_until_complete(self.get_cli_type())
        except RuntimeError:
            return "claude_code"

    async def set_cli_type(self, cli_type: str) -> bool:
        """设置默认 CLI 类型"""
        valid_types = ["claude_code", "codex", "gemini"]
        if cli_type not in valid_types:
            raise ValueError(f"不支持的 CLI 类型: {cli_type}，支持: {', '.join(valid_types)}")
        return await self.set_setting("default_cli", cli_type)

    async def get_review_cli_type(self) -> str:
        """获取 Review 阶段使用的 CLI 类型"""
        value = await self.get_setting("review_cli")
        return value or "codex"

    async def set_review_cli_type(self, cli_type: str) -> bool:
        """设置 Review 阶段使用的 CLI 类型"""
        valid_types = ["claude_code", "codex", "gemini"]
        if cli_type not in valid_types:
            raise ValueError(f"不支持的 CLI 类型: {cli_type}，支持: {', '.join(valid_types)}")
        return await self.set_setting("review_cli", cli_type)

    async def get_review_enabled(self) -> bool:
        """获取是否启用审查功能"""
        value = await self.get_setting("review_enabled")
        # 支持多种格式: "true", "1", "True", "TRUE" 等
        return value is not None and value.lower() in ("true", "1", "yes", "on")

    async def set_review_enabled(self, enabled: bool) -> bool:
        """设置是否启用审查功能"""
        return await self.set_setting("review_enabled", "true" if enabled else "false")

    async def get_max_concurrent_sessions(self) -> int:
        """获取最大并发会话数"""
        value = await self.get_setting("max_concurrent_sessions")
        try:
            return int(value) if value else 3
        except ValueError:
            return 3

    async def set_max_concurrent_sessions(self, count: int) -> bool:
        """设置最大并发会话数"""
        if count < 1:
            raise ValueError("最大并发会话数必须 >= 1")
        if count > 10:
            raise ValueError("最大并发会话数不能超过 10")
        return await self.set_setting("max_concurrent_sessions", str(count))

    async def get_language(self) -> str:
        """获取界面语言设置"""
        value = await self.get_setting("language")
        return value or "zh"

    async def set_language(self, language: str) -> bool:
        """设置界面语言"""
        valid_languages = ["zh", "en"]
        if language not in valid_languages:
            raise ValueError(f"不支持的语言: {language}，支持: {', '.join(valid_languages)}")
        return await self.set_setting("language", language)
