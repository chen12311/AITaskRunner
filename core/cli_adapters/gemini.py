"""
Google Gemini CLI 适配器
"""
import asyncio
import shutil
from typing import Optional

from .base import CLIAdapter, CLIConfig, CLIStatus, CLIType


class GeminiAdapter(CLIAdapter):
    """Google Gemini CLI 适配器"""

    def __init__(self):
        super().__init__()
        self._gemini_path = shutil.which("gemini") or "gemini"

    @property
    def name(self) -> str:
        return "Google Gemini CLI"

    @property
    def cli_type(self) -> CLIType:
        return CLIType.GEMINI

    @property
    def config(self) -> CLIConfig:
        if self._config is None:
            self._config = CLIConfig(
                cli_type=CLIType.GEMINI,
                command=self._gemini_path,
                # yolo 完全自动模式，跳过所有确认
                auto_approve_flag="-y",
                clear_command="/clear",  # Gemini 支持 /clear
                status_command=None,  # Gemini 不支持状态查询
                resume_flag="--resume",
                extra_args=[]
            )
        return self._config

    def get_start_command(self, project_dir: str = None) -> str:
        """
        获取启动命令

        Gemini 交互模式启动
        """
        cmd = f"{self.config.command} {self.config.auto_approve_flag}"
        return cmd

    def get_start_command_with_prompt(self, prompt: str) -> str:
        """
        获取带初始提示的非交互启动命令

        Gemini 支持: gemini -p "your prompt" 或 gemini --prompt "your prompt"
        """
        # 转义引号
        escaped_prompt = prompt.replace('"', '\\"')
        cmd = f'{self.config.command} {self.config.auto_approve_flag} -p "{escaped_prompt}"'
        return cmd

    def get_clear_session_command(self) -> Optional[str]:
        """获取清空会话命令"""
        return self.config.clear_command

    async def get_status(self) -> CLIStatus:
        """
        Gemini 不支持状态查询

        返回默认的运行状态（假设运行中）
        """
        return CLIStatus(
            is_running=True,
            session_id=None,
            context_tokens=0,
            max_tokens=1000000,  # Gemini 2.0 支持 100万 token
            context_usage=0.0,
            extra_info={"note": "Gemini CLI does not support status query"}
        )

    def supports_status_check(self) -> bool:
        """Gemini 不支持状态查询"""
        return False

    def supports_session_resume(self) -> bool:
        """Gemini 支持会话恢复"""
        return True

    def get_resume_command(self) -> str:
        """获取恢复会话命令"""
        return f"{self.config.command} {self.config.resume_flag}"

    def is_available(self) -> bool:
        """检查 Gemini CLI 是否可用"""
        return shutil.which("gemini") is not None

    def format_initial_prompt(self, prompt: str) -> str:
        """
        格式化初始提示词

        Gemini 可以直接接收提示，无需特殊格式
        """
        return prompt
