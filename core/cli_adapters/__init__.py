"""
CLI 适配器模块 - 支持多种 AI CLI 工具
"""
from .base import CLIAdapter, CLIConfig, CLIStatus, CLIType
from .claude_code import ClaudeCodeAdapter
from .codex import CodexAdapter
from .gemini import GeminiAdapter

__all__ = [
    'CLIAdapter',
    'CLIConfig',
    'CLIStatus',
    'CLIType',
    'ClaudeCodeAdapter',
    'CodexAdapter',
    'GeminiAdapter',
]


def get_cli_adapter(cli_type: str) -> CLIAdapter:
    """
    根据类型获取 CLI 适配器

    Args:
        cli_type: CLI 类型字符串 ("claude_code", "codex", "gemini")

    Returns:
        对应的 CLI 适配器实例

    Raises:
        ValueError: 不支持的 CLI 类型
    """
    adapters = {
        "claude_code": ClaudeCodeAdapter,
        "codex": CodexAdapter,
        "gemini": GeminiAdapter,
    }

    if cli_type not in adapters:
        raise ValueError(f"不支持的 CLI 类型: {cli_type}，支持的类型: {list(adapters.keys())}")

    return adapters[cli_type]()


def get_available_cli_types() -> list:
    """
    获取所有可用的 CLI 类型

    Returns:
        可用的 CLI 类型列表
    """
    available = []
    for cli_type in ["claude_code", "codex", "gemini"]:
        try:
            adapter = get_cli_adapter(cli_type)
            if adapter.is_available():
                available.append({
                    "type": cli_type,
                    "name": adapter.name,
                    "supports_status": adapter.supports_status_check(),
                    "supports_resume": adapter.supports_session_resume(),
                })
        except Exception:
            pass
    return available
