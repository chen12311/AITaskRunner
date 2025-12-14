"""
OpenAI Codex CLI 适配器
"""
import asyncio
import shutil
from typing import Optional

from .base import CLIAdapter, CLIConfig, CLIStatus, CLIType


class CodexAdapter(CLIAdapter):
    """OpenAI Codex CLI 适配器"""

    def __init__(self):
        super().__init__()
        self._codex_path = shutil.which("codex") or "codex"

    @property
    def name(self) -> str:
        return "OpenAI Codex CLI"

    @property
    def cli_type(self) -> CLIType:
        return CLIType.CODEX

    @property
    def config(self) -> CLIConfig:
        if self._config is None:
            self._config = CLIConfig(
                cli_type=CLIType.CODEX,
                command=self._codex_path,
                # --yolo 完全自动模式，跳过所有确认
                auto_approve_flag="--yolo",
                clear_command=None,  # Codex 不支持 /clear
                status_command=None,  # Codex 不支持状态查询
                resume_flag="resume --last",
                extra_args=[]
            )
        return self._config

    def get_start_command(self, project_dir: str = None) -> str:
        """
        获取启动命令

        Codex 可以直接带初始提示启动，但交互模式下我们先启动空会话
        """
        cmd = f"{self.config.command} {self.config.auto_approve_flag}"
        return cmd

    def get_start_command_with_prompt(self, prompt: str) -> str:
        """
        获取带初始提示的启动命令

        Codex 支持: codex --full-auto "your prompt here"
        """
        # 转义引号
        escaped_prompt = prompt.replace('"', '\\"')
        cmd = f'{self.config.command} {self.config.auto_approve_flag} "{escaped_prompt}"'
        return cmd

    def get_clear_session_command(self) -> Optional[str]:
        """Codex 不支持清空会话命令"""
        return None

    async def get_status(self) -> CLIStatus:
        """
        Codex 不支持状态查询

        返回默认的运行状态（假设运行中）
        """
        return CLIStatus(
            is_running=True,
            session_id=None,
            context_tokens=0,
            max_tokens=128000,  # Codex 默认上下文
            context_usage=0.0,
            extra_info={"note": "Codex CLI does not support status query"}
        )

    def supports_status_check(self) -> bool:
        """Codex 不支持状态查询"""
        return False

    def supports_session_resume(self) -> bool:
        """Codex 支持会话恢复"""
        return True

    def get_resume_command(self) -> str:
        """获取恢复会话命令"""
        return f"{self.config.command} {self.config.resume_flag}"

    def is_available(self) -> bool:
        """检查 Codex CLI 是否可用"""
        return shutil.which("codex") is not None

    def format_initial_prompt(self, prompt: str) -> str:
        """
        格式化初始提示词

        Codex 可以直接接收提示，无需特殊格式
        """
        return prompt
