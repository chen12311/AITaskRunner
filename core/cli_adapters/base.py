"""
CLI 适配器基类 - 定义不同 AI CLI 工具的抽象接口
支持 Claude Code、OpenAI Codex CLI、Google Gemini CLI
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class CLIType(Enum):
    """CLI 类型枚举"""
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    GEMINI = "gemini"


@dataclass
class CLIConfig:
    """CLI 配置"""
    cli_type: CLIType
    command: str  # 基础命令，如 "claude", "codex", "gemini"
    auto_approve_flag: str  # 自动批准标志
    clear_command: Optional[str] = None  # 清空会话命令
    status_command: Optional[str] = None  # 状态查询命令
    resume_flag: Optional[str] = None  # 会话恢复标志
    extra_args: list = field(default_factory=list)  # 额外参数


@dataclass
class CLIStatus:
    """CLI 运行状态"""
    is_running: bool
    session_id: Optional[str] = None
    context_tokens: int = 0
    max_tokens: int = 200000
    context_usage: float = 0.0  # 0.0 - 1.0
    extra_info: Dict[str, Any] = field(default_factory=dict)


class CLIAdapter(ABC):
    """CLI 适配器抽象基类"""

    def __init__(self):
        self._config: Optional[CLIConfig] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """CLI 名称"""
        pass

    @property
    @abstractmethod
    def cli_type(self) -> CLIType:
        """CLI 类型"""
        pass

    @property
    @abstractmethod
    def config(self) -> CLIConfig:
        """获取 CLI 配置"""
        pass

    @abstractmethod
    def get_start_command(self, project_dir: str = None) -> str:
        """
        获取启动命令

        Args:
            project_dir: 项目目录

        Returns:
            完整的启动命令字符串
        """
        pass

    @abstractmethod
    def get_clear_session_command(self) -> Optional[str]:
        """
        获取清空会话的命令

        Returns:
            清空命令，如 "/clear"，不支持则返回 None
        """
        pass

    @abstractmethod
    async def get_status(self) -> CLIStatus:
        """
        获取 CLI 运行状态

        Returns:
            CLIStatus 对象
        """
        pass

    @abstractmethod
    def supports_status_check(self) -> bool:
        """
        是否支持状态查询

        Returns:
            True 如果支持实时状态查询
        """
        pass

    @abstractmethod
    def supports_session_resume(self) -> bool:
        """
        是否支持会话恢复

        Returns:
            True 如果支持通过命令恢复会话
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查 CLI 是否已安装且可用

        Returns:
            是否可用
        """
        pass

    def get_env_vars(self, task_id: str = None, api_base_url: str = None) -> Dict[str, str]:
        """
        获取需要设置的环境变量

        Args:
            task_id: 任务ID
            api_base_url: API 基础 URL

        Returns:
            环境变量字典
        """
        env_vars = {}
        if task_id:
            env_vars["CODEX_TASK_ID"] = task_id
        if api_base_url:
            env_vars["CODEX_API_BASE_URL"] = api_base_url
        return env_vars

    def format_initial_prompt(self, prompt: str) -> str:
        """
        格式化初始提示词（不同 CLI 可能有不同格式要求）

        Args:
            prompt: 原始提示词

        Returns:
            格式化后的提示词
        """
        return prompt
