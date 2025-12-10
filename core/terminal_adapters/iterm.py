"""
iTerm2 终端适配器 - 使用 AppleScript 控制（需要短暂聚焦窗口）
"""
import asyncio
import os
from typing import Optional
from .base import TerminalAdapter, TerminalSession


class iTermAdapter(TerminalAdapter):
    """iTerm2 终端适配器"""

    @property
    def name(self) -> str:
        return "iTerm"

    def is_available(self) -> bool:
        """检查 iTerm2 是否已安装"""
        return os.path.exists("/Applications/iTerm.app")

    async def create_window(
        self,
        project_dir: str,
        command: str,
        task_id: Optional[str] = None,
        api_base_url: Optional[str] = None
    ) -> Optional[TerminalSession]:
        """
        创建新的 iTerm 窗口并执行命令
        """
        try:
            # 转义 AppleScript 特殊字符
            project_dir_escaped = project_dir.replace('"', '\\"')
            command_escaped = command.replace('"', '\\"')

            # 构建环境变量设置命令（用于 Stop hook）
            env_commands = []
            if task_id:
                env_commands.append(f"export CODEX_TASK_ID='{task_id}'")
            if api_base_url:
                env_commands.append(f"export CODEX_API_BASE_URL='{api_base_url}'")

            # 使用 AppleScript 创建窗口（不激活，避免打断用户）
            env_write_statements = ""
            for env_cmd in env_commands:
                env_cmd_escaped = env_cmd.replace('"', '\\"')
                env_write_statements += f'''
                    write text "{env_cmd_escaped}"
                    delay 0.2'''

            applescript = f'''
            tell application "iTerm"
                set newWindow to (create window with default profile)
                tell current session of newWindow
                    write text "cd \\"{project_dir_escaped}\\""
                    delay 0.5{env_write_statements}
                    write text "{command_escaped}"
                    delay 1.5
                end tell
                return (id of newWindow)
            end tell
            '''

            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
                returncode = process.returncode
                stderr_text = stderr.decode('utf-8')
                window_id = stdout.decode('utf-8').strip()
            except asyncio.TimeoutError:
                process.kill()
                print(f"❌ iTerm AppleScript 执行超时")
                return None

            if returncode != 0:
                print(f"❌ iTerm AppleScript 执行失败: {stderr_text}")
                return None

            # 等待命令启动
            await asyncio.sleep(1)

            self.current_session = TerminalSession(
                session_id=window_id or "unknown",
                window_id=window_id
            )

            print(f"✅ iTerm 窗口已创建，window_id: {window_id}")
            return self.current_session

        except Exception as e:
            print(f"❌ 创建 iTerm 窗口失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def send_text(self, text: str, press_enter: bool = True) -> bool:
        """
        发送文本到 iTerm - 需要短暂切换焦点后自动切回

        由于 macOS 限制，按键模拟必须在窗口聚焦状态下进行
        """
        if not self.current_session:
            print("❌ 没有活跃的 iTerm 会话")
            return False

        try:
            # 1. 保存当前剪贴板内容
            process = await asyncio.create_subprocess_exec(
                'pbpaste',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=2)
                saved_clipboard = stdout.decode('utf-8')
            except asyncio.TimeoutError:
                process.kill()
                saved_clipboard = ""

            # 2. 将文本复制到剪贴板
            process = await asyncio.create_subprocess_exec(
                'pbcopy',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                await asyncio.wait_for(process.communicate(input=text.encode('utf-8')), timeout=2)
            except asyncio.TimeoutError:
                process.kill()

            # 3. 构建 AppleScript - 短暂切换焦点，发送后切回
            window_id = self.current_session.window_id

            if press_enter:
                keystroke_script = '''
    keystroke "v" using {command down}
    delay 0.1
    keystroke return
'''
            else:
                keystroke_script = '''
    keystroke "v" using {command down}
'''

            if window_id:
                applescript = f'''
set frontApp to path to frontmost application as text
tell application "iTerm"
    tell window id {window_id}
        select
    end tell
    activate
end tell
delay 0.1
tell application "System Events"
{keystroke_script}
end tell
delay 0.1
activate application frontApp
'''
            else:
                applescript = f'''
set frontApp to path to frontmost application as text
tell application "iTerm"
    activate
end tell
delay 0.1
tell application "System Events"
{keystroke_script}
end tell
delay 0.1
activate application frontApp
'''

            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
                returncode = process.returncode
                stderr_text = stderr.decode('utf-8')
            except asyncio.TimeoutError:
                process.kill()
                print(f"❌ iTerm 发送文本超时")
                return False

            # 4. 恢复原剪贴板内容
            process = await asyncio.create_subprocess_exec(
                'pbcopy',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                await asyncio.wait_for(process.communicate(input=saved_clipboard.encode('utf-8')), timeout=2)
            except asyncio.TimeoutError:
                process.kill()

            if returncode != 0:
                print(f"❌ iTerm 发送文本失败: {stderr_text}")
                return False

            print(f"✅ 已发送文本到 iTerm")
            return True

        except Exception as e:
            print(f"❌ 发送文本到 iTerm 失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def close_window(self) -> bool:
        """关闭 iTerm 窗口"""
        if not self.current_session:
            return True

        try:
            window_id = self.current_session.window_id

            if window_id:
                applescript = f'''
tell application "iTerm"
    close window id {window_id}
end tell
'''
                process = await asyncio.create_subprocess_exec(
                    'osascript', '-e', applescript,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                try:
                    await asyncio.wait_for(process.communicate(), timeout=3)
                except asyncio.TimeoutError:
                    process.kill()

            self.clear_session()
            print("✅ iTerm 窗口已关闭")
            return True

        except Exception as e:
            print(f"⚠️ 关闭 iTerm 窗口失败: {e}")
            self.clear_session()
            return False
