"""
Claude Code监控器 - 向后兼容模块
已迁移到 cli_monitor.py，此文件保留以支持旧代码

新代码请使用:
    from core.cli_monitor import CLIMonitor, CLIStatus
"""
from core.cli_monitor import CLIMonitor, CLIStatus

# 向后兼容别名
CodexMonitor = CLIMonitor
CodexStatus = CLIStatus

__all__ = ['CodexMonitor', 'CodexStatus', 'CLIMonitor', 'CLIStatus']
