"""
会话管理模块 - 支持多项目并行运行

提供会话池架构，每个任务拥有独立的会话实例。
"""
from core.session.models import SessionStatus, ManagedSession
from core.session.manager import SessionManager

__all__ = [
    "SessionStatus",
    "ManagedSession",
    "SessionManager",
]
