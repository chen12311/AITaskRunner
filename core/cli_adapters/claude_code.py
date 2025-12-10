"""
Claude Code CLI 适配器
"""
import asyncio
import json
import shutil
from typing import Optional
from pathlib import Path

from .base import CLIAdapter, CLIConfig, CLIStatus, CLIType


class ClaudeCodeAdapter(CLIAdapter):
    """Claude Code CLI 适配器"""

    def __init__(self):
        super().__init__()
        # Claude 可执行文件路径
        self._claude_path = self._find_claude_path()

    def _find_claude_path(self) -> str:
        """查找 Claude 可执行文件路径"""
        # 优先使用用户目录下的 claude
        user_claude = Path.home() / ".claude" / "local" / "claude"
        if user_claude.exists():
            return str(user_claude)

        # 尝试从 PATH 中查找
        claude_in_path = shutil.which("claude")
        if claude_in_path:
            return claude_in_path

        # 默认返回用户目录路径
        return str(user_claude)

    @property
    def name(self) -> str:
        return "Claude Code"

    @property
    def cli_type(self) -> CLIType:
        return CLIType.CLAUDE_CODE

    @property
    def config(self) -> CLIConfig:
        if self._config is None:
            self._config = CLIConfig(
                cli_type=CLIType.CLAUDE_CODE,
                command=self._claude_path,
                auto_approve_flag="--dangerously-skip-permissions",
                clear_command="/clear",
                status_command="status --format json",
                resume_flag=None,  # Claude Code 通过 /clear 重新开始
                extra_args=[]
            )
        return self._config

    def get_start_command(self, project_dir: str = None) -> str:
        """获取启动命令"""
        cmd = f"{self.config.command} {self.config.auto_approve_flag}"
        return cmd

    def get_clear_session_command(self) -> Optional[str]:
        """获取清空会话命令"""
        return self.config.clear_command

    async def get_status(self) -> CLIStatus:
        """获取 Claude Code 运行状态"""
        try:
            process = await asyncio.create_subprocess_exec(
                self._claude_path, "status", "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
                returncode = process.returncode
                stdout_text = stdout.decode('utf-8')
            except asyncio.TimeoutError:
                process.kill()
                return CLIStatus(is_running=False)

            if returncode == 0:
                status_data = json.loads(stdout_text)
                context_tokens = status_data.get('context_tokens', 0)
                max_tokens = status_data.get('max_context_tokens', 200000)

                return CLIStatus(
                    is_running=True,
                    session_id=status_data.get('session_id'),
                    context_tokens=context_tokens,
                    max_tokens=max_tokens,
                    context_usage=context_tokens / max_tokens if max_tokens > 0 else 0,
                    extra_info=status_data
                )
            else:
                return CLIStatus(is_running=False)

        except Exception as e:
            print(f"⚠️ 获取 Claude Code 状态失败: {e}")
            return CLIStatus(is_running=False)

    def supports_status_check(self) -> bool:
        """Claude Code 支持状态查询"""
        return True

    def supports_session_resume(self) -> bool:
        """Claude Code 不支持命令行恢复会话，通过 /clear 重新开始"""
        return False

    def is_available(self) -> bool:
        """检查 Claude Code 是否可用"""
        return Path(self._claude_path).exists() or shutil.which("claude") is not None
