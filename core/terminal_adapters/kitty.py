"""
Kitty 终端适配器 - 使用远程控制 API 实现后台操作（无需聚焦窗口）
"""
import asyncio
import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional
from .base import TerminalAdapter, TerminalSession


class KittyAdapter(TerminalAdapter):
    """Kitty 终端适配器 - 支持后台发送文本"""

    def __init__(self):
        super().__init__()
        self._socket_dir = tempfile.gettempdir()  # 跨平台临时目录

    @property
    def name(self) -> str:
        return "Kitty"

    def is_available(self) -> bool:
        """检查 Kitty 是否已安装"""
        # 检查常见安装路径
        paths = [
            "/Applications/kitty.app/Contents/MacOS/kitty",
            "/usr/local/bin/kitty",
            os.path.expanduser("~/.local/kitty.app/bin/kitty"),
        ]
        for path in paths:
            if os.path.exists(path):
                return True

        # 尝试 which 命令
        try:
            result = os.popen("which kitty").read().strip()
            return bool(result)
        except:
            return False

    def _get_kitty_path(self) -> str:
        """获取 kitty 可执行文件路径"""
        paths = [
            "/Applications/kitty.app/Contents/MacOS/kitty",
            "/usr/local/bin/kitty",
            os.path.expanduser("~/.local/kitty.app/bin/kitty"),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return "kitty"  # 假设在 PATH 中

    def _get_kitten_path(self) -> str:
        """获取 kitten 可执行文件路径（用于远程控制）"""
        # kitten 通常和 kitty 在同一目录
        kitty_path = self._get_kitty_path()
        if kitty_path.endswith("/kitty"):
            kitten_path = kitty_path.replace("/kitty", "/kitten")
            if os.path.exists(kitten_path):
                return kitten_path
        return "kitten"

    async def create_window(
        self,
        project_dir: str,
        command: str,
        task_id: Optional[str] = None,
        api_base_url: Optional[str] = None
    ) -> Optional[TerminalSession]:
        """
        创建新的 Kitty 窗口并执行命令

        使用 --listen-on 参数启动 Kitty，以便后续可以通过 socket 发送命令
        """
        try:
            # 生成唯一的 socket 路径（跨平台）
            session_id = str(uuid.uuid4())[:8]
            socket_path = str(Path(self._socket_dir) / f"kitty-codex-{session_id}")

            kitty_path = self._get_kitty_path()

            # 构建环境变量设置命令（用于 Stop hook）
            env_setup = ""
            if task_id:
                env_setup += f"export CODEX_TASK_ID='{task_id}'; "
            if api_base_url:
                env_setup += f"export CODEX_API_BASE_URL='{api_base_url}'; "

            # 完整命令：设置环境变量 + 执行 Claude Code
            full_command = f"{env_setup}{command}"

            # 启动 Kitty 窗口，启用远程控制
            # --listen-on: 指定 socket 路径
            # --directory: 设置工作目录
            # -o allow_remote_control=socket-only: 只允许通过 socket 远程控制
            process = await asyncio.create_subprocess_exec(
                kitty_path,
                "--listen-on", f"unix:{socket_path}",
                "--directory", project_dir,
                "-o", "allow_remote_control=socket-only",
                "-e", "/bin/zsh", "-c", f"{full_command}; exec /bin/zsh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 等待 socket 文件创建
            for _ in range(20):  # 最多等待 2 秒
                await asyncio.sleep(0.1)
                if os.path.exists(socket_path):
                    break
            else:
                print(f"⚠️ Kitty socket 文件未创建: {socket_path}")

            # 额外等待命令启动
            await asyncio.sleep(1.5)

            self.current_session = TerminalSession(
                session_id=session_id,
                socket_path=socket_path
            )

            print(f"✅ Kitty 窗口已创建，socket: {socket_path}")
            return self.current_session

        except Exception as e:
            print(f"❌ 创建 Kitty 窗口失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def send_text(self, text: str, press_enter: bool = True) -> bool:
        """
        发送文本到 Kitty - 通过远程控制 API（无需聚焦窗口）

        使用 send-text 发送文本，再用 send-key 发送 Enter 键
        """
        if not self.current_session or not self.current_session.socket_path:
            print("❌ 没有活跃的 Kitty 会话")
            return False

        try:
            socket_path = self.current_session.socket_path
            kitten_path = self._get_kitten_path()

            # 1. 使用 kitten @ send-text 发送文本
            process = await asyncio.create_subprocess_exec(
                kitten_path, "@",
                "--to", f"unix:{socket_path}",
                "send-text", "--",
                text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
                returncode = process.returncode

                if returncode != 0:
                    stderr_text = stderr.decode('utf-8')
                    print(f"❌ Kitty send-text 失败: {stderr_text}")
                    return False

            except asyncio.TimeoutError:
                process.kill()
                print(f"❌ Kitty send-text 超时")
                return False

            # 2. 如果需要回车，使用 send-key 发送 Enter 键
            if press_enter:
                await asyncio.sleep(0.1)  # 短暂等待确保文本已发送

                process = await asyncio.create_subprocess_exec(
                    kitten_path, "@",
                    "--to", f"unix:{socket_path}",
                    "send-key", "Enter",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
                    returncode = process.returncode

                    if returncode != 0:
                        stderr_text = stderr.decode('utf-8')
                        print(f"❌ Kitty send-key 失败: {stderr_text}")
                        return False

                except asyncio.TimeoutError:
                    process.kill()
                    print(f"❌ Kitty send-key 超时")
                    return False

            print(f"✅ 已发送文本到 Kitty（后台）")
            return True

        except Exception as e:
            print(f"❌ 发送文本到 Kitty 失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def is_window_alive(self) -> bool:
        """
        检查 Kitty 窗口是否存活

        通过检查 socket 文件是否存在来判断
        """
        if not self.current_session or not self.current_session.socket_path:
            return False
        return os.path.exists(self.current_session.socket_path)

    async def close_window(self) -> bool:
        """关闭 Kitty 窗口"""
        if not self.current_session:
            return True

        try:
            socket_path = self.current_session.socket_path
            if socket_path and os.path.exists(socket_path):
                kitten_path = self._get_kitten_path()

                # 使用 kitten @ close-window 关闭窗口
                process = await asyncio.create_subprocess_exec(
                    kitten_path, "@",
                    "--to", f"unix:{socket_path}",
                    "close-window",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                try:
                    await asyncio.wait_for(process.communicate(), timeout=3)
                except asyncio.TimeoutError:
                    process.kill()

                # 清理 socket 文件
                try:
                    os.remove(socket_path)
                except:
                    pass

            self.clear_session()
            print("✅ Kitty 窗口已关闭")
            return True

        except Exception as e:
            print(f"⚠️ 关闭 Kitty 窗口失败: {e}")
            self.clear_session()
            return False
