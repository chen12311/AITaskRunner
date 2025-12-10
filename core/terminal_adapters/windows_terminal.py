"""
Windows Terminal 适配器 - 使用 wt.exe 命令行控制
支持 Windows 10/11 的 Windows Terminal
"""
import asyncio
import subprocess
import json
from typing import Optional
from .base import TerminalAdapter, TerminalSession


class WindowsTerminalAdapter(TerminalAdapter):
    """Windows Terminal 适配器"""

    def __init__(self):
        super().__init__()
        self._process_id: Optional[int] = None

    @property
    def name(self) -> str:
        return "Windows Terminal"

    def is_available(self) -> bool:
        """检查 Windows Terminal 是否已安装"""
        try:
            # 尝试运行 wt.exe --version
            result = subprocess.run(
                ["wt.exe", "--version"],
                capture_output=True,
                timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # 备选：检查 where 命令
            try:
                result = subprocess.run(
                    ["where", "wt"],
                    capture_output=True,
                    timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                return result.returncode == 0
            except:
                return False

    async def _run_powershell(self, script: str) -> tuple[bool, str, str]:
        """
        运行 PowerShell 脚本

        Returns:
            (success, stdout, stderr)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10
                )
                return (
                    process.returncode == 0,
                    stdout.decode('utf-8', errors='ignore').strip(),
                    stderr.decode('utf-8', errors='ignore').strip()
                )
            except asyncio.TimeoutError:
                process.kill()
                return False, "", "PowerShell 执行超时"

        except Exception as e:
            return False, "", str(e)

    async def create_window(
        self,
        project_dir: str,
        command: str,
        task_id: Optional[str] = None,
        api_base_url: Optional[str] = None
    ) -> Optional[TerminalSession]:
        """
        创建新的 Windows Terminal 窗口并执行命令

        使用 wt.exe 命令行参数创建新窗口
        """
        try:
            # 转义路径中的特殊字符
            project_dir_escaped = project_dir.replace('"', '`"')
            command_escaped = command.replace('"', '`"')

            # 构建环境变量设置命令
            env_commands = []
            if task_id:
                env_commands.append(f"$env:CODEX_TASK_ID='{task_id}'")
            if api_base_url:
                env_commands.append(f"$env:CODEX_API_BASE_URL='{api_base_url}'")

            # 组合完整命令：设置环境变量 + 执行 CLI 命令 + 保持窗口打开
            env_setup = "; ".join(env_commands) if env_commands else ""
            full_command = f"{env_setup}; {command_escaped}; Read-Host 'Press Enter to exit'"

            # 使用 wt.exe 创建新窗口
            # -w -1: 创建新窗口（而不是新标签页）
            # --title: 设置窗口标题
            # -d: 设置工作目录
            # powershell.exe -NoExit -Command: 执行命令并保持窗口打开
            wt_args = [
                "wt.exe",
                "-w", "-1",  # 新窗口
                "--title", f"Codex Automation - Task {task_id or 'Unknown'}",
                "-d", project_dir,
                "powershell.exe",
                "-NoExit",
                "-Command",
                full_command
            ]

            print(f"🚀 启动 Windows Terminal 窗口")
            print(f"   工作目录: {project_dir}")
            print(f"   命令: {command}")

            # 启动 Windows Terminal
            process = await asyncio.create_subprocess_exec(
                *wt_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            # 等待窗口创建
            await asyncio.sleep(2)

            # 创建会话信息
            session_id = task_id or f"wt-{id(self)}"
            self.current_session = TerminalSession(
                session_id=session_id,
                window_id=session_id
            )
            self._process_id = process.pid

            print(f"✅ Windows Terminal 窗口已创建")
            return self.current_session

        except Exception as e:
            print(f"❌ 创建 Windows Terminal 窗口失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def send_text(self, text: str, press_enter: bool = True) -> bool:
        """
        发送文本到 Windows Terminal

        使用剪贴板 + SendKeys 方法（类似 iTerm2 实现）
        """
        if not self.current_session:
            print("❌ 没有活跃的 Windows Terminal 会话")
            return False

        try:
            # 1. 保存当前剪贴板内容
            success, saved_clipboard, error = await self._run_powershell("Get-Clipboard -Raw")
            if not success:
                print(f"⚠️ 无法读取剪贴板: {error}")
                saved_clipboard = ""

            # 2. 将文本写入剪贴板（处理特殊字符）
            text_escaped = text.replace("'", "''")  # PowerShell 单引号转义
            set_clipboard_script = f"Set-Clipboard -Value '{text_escaped}'"
            success, _, error = await self._run_powershell(set_clipboard_script)
            if not success:
                print(f"❌ 写入剪贴板失败: {error}")
                return False

            # 3. 激活 Windows Terminal 并发送 Ctrl+V
            # 使用 SendKeys 发送按键
            if press_enter:
                sendkeys_script = """
$wshell = New-Object -ComObject wscript.shell
if ($wshell.AppActivate("Windows Terminal") -or $wshell.AppActivate("Codex Automation")) {
    Start-Sleep -Milliseconds 200
    $wshell.SendKeys("^v")
    Start-Sleep -Milliseconds 100
    $wshell.SendKeys("{ENTER}")
} else {
    Write-Error "无法激活 Windows Terminal 窗口"
    exit 1
}
"""
            else:
                sendkeys_script = """
$wshell = New-Object -ComObject wscript.shell
if ($wshell.AppActivate("Windows Terminal") -or $wshell.AppActivate("Codex Automation")) {
    Start-Sleep -Milliseconds 200
    $wshell.SendKeys("^v")
} else {
    Write-Error "无法激活 Windows Terminal 窗口"
    exit 1
}
"""

            success, _, error = await self._run_powershell(sendkeys_script)
            if not success:
                print(f"❌ 发送按键失败: {error}")
                return False

            # 4. 恢复原剪贴板内容
            if saved_clipboard:
                saved_escaped = saved_clipboard.replace("'", "''")
                await self._run_powershell(f"Set-Clipboard -Value '{saved_escaped}'")

            print(f"✅ 已发送文本到 Windows Terminal")
            return True

        except Exception as e:
            print(f"❌ 发送文本到 Windows Terminal 失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def close_window(self) -> bool:
        """关闭 Windows Terminal 窗口"""
        if not self.current_session:
            return True

        try:
            # 尝试通过 taskkill 关闭窗口
            # 注意：这会关闭整个 Windows Terminal 进程，如果有多个标签页可能会影响其他标签页
            # 更温和的方法是发送 Alt+F4 或 Ctrl+Shift+W，但需要窗口聚焦
            if self._process_id:
                close_script = f"Stop-Process -Id {self._process_id} -Force -ErrorAction SilentlyContinue"
                await self._run_powershell(close_script)
            else:
                # 备选：关闭所有包含特定标题的 Windows Terminal 窗口
                close_script = """
$wshell = New-Object -ComObject wscript.shell
if ($wshell.AppActivate("Codex Automation")) {
    Start-Sleep -Milliseconds 200
    $wshell.SendKeys("%{F4}")
}
"""
                await self._run_powershell(close_script)

            self.clear_session()
            self._process_id = None
            print("✅ Windows Terminal 窗口已关闭")
            return True

        except Exception as e:
            print(f"⚠️ 关闭 Windows Terminal 窗口失败: {e}")
            self.clear_session()
            self._process_id = None
            return False
