"""
终端适配器基类 - 定义终端操作的抽象接口
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class TerminalSession:
    """终端会话信息"""
    session_id: str
    window_id: Optional[str] = None
    socket_path: Optional[str] = None


class TerminalAdapter(ABC):
    """终端适配器抽象基类"""

    def __init__(self):
        self.current_session: Optional[TerminalSession] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """终端名称"""
        pass

    @abstractmethod
    async def create_window(
        self,
        project_dir: str,
        command: str,
        task_id: Optional[str] = None,
        api_base_url: Optional[str] = None
    ) -> Optional[TerminalSession]:
        """
        创建新的终端窗口并执行命令

        Args:
            project_dir: 工作目录
            command: 要执行的命令
            task_id: 任务ID（用于 Stop hook 环境变量）
            api_base_url: API基础URL（用于 Stop hook 环境变量）

        Returns:
            会话信息，失败返回 None
        """
        pass

    @abstractmethod
    async def send_text(self, text: str, press_enter: bool = True) -> bool:
        """
        发送文本到终端

        Args:
            text: 要发送的文本
            press_enter: 是否在末尾发送回车

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def close_window(self) -> bool:
        """
        关闭当前窗口

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查终端是否可用（已安装）

        Returns:
            是否可用
        """
        pass

    def has_active_session(self) -> bool:
        """是否有活跃会话"""
        return self.current_session is not None

    def is_window_alive(self) -> bool:
        """
        检查终端窗口是否真的存活

        子类应覆盖此方法实现实际检查
        默认返回 has_active_session() 的结果
        """
        return self.has_active_session()

    def clear_session(self):
        """清除会话信息"""
        self.current_session = None

    async def is_cli_active(self) -> Optional[bool]:
        """
        检测 CLI 是否在活跃执行

        子类可覆盖此方法实现终端特定的检测逻辑。
        默认返回 None 表示不支持此功能。

        Returns:
            True = CLI 在活跃执行
            False = CLI 不活跃
            None = 不支持此功能（回退到心跳检测）
        """
        return None
