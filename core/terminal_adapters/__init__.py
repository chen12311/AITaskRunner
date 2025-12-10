"""
终端适配器模块 - 支持 iTerm、Kitty 和 Windows Terminal
"""
import platform
from .base import TerminalAdapter
from .iterm import iTermAdapter
from .kitty import KittyAdapter
from .windows_terminal import WindowsTerminalAdapter

__all__ = ['TerminalAdapter', 'iTermAdapter', 'KittyAdapter', 'WindowsTerminalAdapter']


def get_available_terminal_adapters():
    """
    获取当前平台可用的终端适配器列表

    Returns:
        list[tuple[str, type]]: [(终端名称, 适配器类), ...]
    """
    system = platform.system()
    available = []

    if system == "Darwin":  # macOS
        # 检查 Kitty
        kitty = KittyAdapter()
        if kitty.is_available():
            available.append(("kitty", KittyAdapter))

        # 检查 iTerm
        iterm = iTermAdapter()
        if iterm.is_available():
            available.append(("iterm", iTermAdapter))

    elif system == "Linux":
        # Linux 主要支持 Kitty
        kitty = KittyAdapter()
        if kitty.is_available():
            available.append(("kitty", KittyAdapter))

    elif system == "Windows":
        # Windows 支持 Windows Terminal
        wt = WindowsTerminalAdapter()
        if wt.is_available():
            available.append(("windows_terminal", WindowsTerminalAdapter))

    return available


def get_default_terminal_adapter():
    """
    获取当前平台的默认终端适配器

    Returns:
        TerminalAdapter 实例或 None
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        # 优先 Kitty，其次 iTerm
        kitty = KittyAdapter()
        if kitty.is_available():
            return kitty

        iterm = iTermAdapter()
        if iterm.is_available():
            return iterm

    elif system == "Linux":
        # Linux 默认 Kitty
        kitty = KittyAdapter()
        if kitty.is_available():
            return kitty

    elif system == "Windows":
        # Windows 默认 Windows Terminal
        wt = WindowsTerminalAdapter()
        if wt.is_available():
            return wt

    return None
