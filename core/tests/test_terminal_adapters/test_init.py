"""
Terminal Adapters __init__ Tests
测试终端适配器模块初始化
"""
import pytest
from unittest.mock import patch, MagicMock

from core.terminal_adapters import (
    get_available_terminal_adapters,
    get_default_terminal_adapter,
    TerminalAdapter,
    iTermAdapter,
    KittyAdapter,
    WindowsTerminalAdapter,
)


class TestGetAvailableTerminalAdapters:
    """测试 get_available_terminal_adapters 函数"""

    def test_darwin_kitty_available(self):
        """测试 macOS 上 Kitty 可用"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = True

        mock_iterm = MagicMock()
        mock_iterm.is_available.return_value = False

        with patch('platform.system', return_value="Darwin"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                with patch('core.terminal_adapters.iTermAdapter', return_value=mock_iterm):
                    available = get_available_terminal_adapters()
                    assert len(available) == 1
                    assert available[0][0] == "kitty"

    def test_darwin_iterm_available(self):
        """测试 macOS 上 iTerm 可用"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = False

        mock_iterm = MagicMock()
        mock_iterm.is_available.return_value = True

        with patch('platform.system', return_value="Darwin"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                with patch('core.terminal_adapters.iTermAdapter', return_value=mock_iterm):
                    available = get_available_terminal_adapters()
                    assert len(available) == 1
                    assert available[0][0] == "iterm"

    def test_darwin_both_available(self):
        """测试 macOS 上两者都可用"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = True

        mock_iterm = MagicMock()
        mock_iterm.is_available.return_value = True

        with patch('platform.system', return_value="Darwin"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                with patch('core.terminal_adapters.iTermAdapter', return_value=mock_iterm):
                    available = get_available_terminal_adapters()
                    assert len(available) == 2

    def test_linux_kitty_available(self):
        """测试 Linux 上 Kitty 可用"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = True

        with patch('platform.system', return_value="Linux"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                available = get_available_terminal_adapters()
                assert len(available) == 1
                assert available[0][0] == "kitty"

    def test_linux_kitty_not_available(self):
        """测试 Linux 上 Kitty 不可用"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = False

        with patch('platform.system', return_value="Linux"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                available = get_available_terminal_adapters()
                assert len(available) == 0

    def test_windows_wt_available(self):
        """测试 Windows 上 Windows Terminal 可用"""
        mock_wt = MagicMock()
        mock_wt.is_available.return_value = True

        with patch('platform.system', return_value="Windows"):
            with patch('core.terminal_adapters.WindowsTerminalAdapter', return_value=mock_wt):
                available = get_available_terminal_adapters()
                assert len(available) == 1
                assert available[0][0] == "windows_terminal"

    def test_windows_wt_not_available(self):
        """测试 Windows 上 Windows Terminal 不可用"""
        mock_wt = MagicMock()
        mock_wt.is_available.return_value = False

        with patch('platform.system', return_value="Windows"):
            with patch('core.terminal_adapters.WindowsTerminalAdapter', return_value=mock_wt):
                available = get_available_terminal_adapters()
                assert len(available) == 0

    def test_unknown_platform(self):
        """测试未知平台"""
        with patch('platform.system', return_value="Unknown"):
            available = get_available_terminal_adapters()
            assert len(available) == 0


class TestGetDefaultTerminalAdapter:
    """测试 get_default_terminal_adapter 函数"""

    def test_darwin_kitty_default(self):
        """测试 macOS 上 Kitty 为默认"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = True

        with patch('platform.system', return_value="Darwin"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                adapter = get_default_terminal_adapter()
                assert adapter is mock_kitty

    def test_darwin_iterm_fallback(self):
        """测试 macOS 上 Kitty 不可用时回退到 iTerm"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = False

        mock_iterm = MagicMock()
        mock_iterm.is_available.return_value = True

        with patch('platform.system', return_value="Darwin"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                with patch('core.terminal_adapters.iTermAdapter', return_value=mock_iterm):
                    adapter = get_default_terminal_adapter()
                    assert adapter is mock_iterm

    def test_darwin_none_available(self):
        """测试 macOS 上没有可用终端"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = False

        mock_iterm = MagicMock()
        mock_iterm.is_available.return_value = False

        with patch('platform.system', return_value="Darwin"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                with patch('core.terminal_adapters.iTermAdapter', return_value=mock_iterm):
                    adapter = get_default_terminal_adapter()
                    assert adapter is None

    def test_linux_kitty_default(self):
        """测试 Linux 上 Kitty 为默认"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = True

        with patch('platform.system', return_value="Linux"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                adapter = get_default_terminal_adapter()
                assert adapter is mock_kitty

    def test_linux_none_available(self):
        """测试 Linux 上没有可用终端"""
        mock_kitty = MagicMock()
        mock_kitty.is_available.return_value = False

        with patch('platform.system', return_value="Linux"):
            with patch('core.terminal_adapters.KittyAdapter', return_value=mock_kitty):
                adapter = get_default_terminal_adapter()
                assert adapter is None

    def test_windows_wt_default(self):
        """测试 Windows 上 Windows Terminal 为默认"""
        mock_wt = MagicMock()
        mock_wt.is_available.return_value = True

        with patch('platform.system', return_value="Windows"):
            with patch('core.terminal_adapters.WindowsTerminalAdapter', return_value=mock_wt):
                adapter = get_default_terminal_adapter()
                assert adapter is mock_wt

    def test_windows_none_available(self):
        """测试 Windows 上没有可用终端"""
        mock_wt = MagicMock()
        mock_wt.is_available.return_value = False

        with patch('platform.system', return_value="Windows"):
            with patch('core.terminal_adapters.WindowsTerminalAdapter', return_value=mock_wt):
                adapter = get_default_terminal_adapter()
                assert adapter is None

    def test_unknown_platform(self):
        """测试未知平台"""
        with patch('platform.system', return_value="Unknown"):
            adapter = get_default_terminal_adapter()
            assert adapter is None


class TestModuleExports:
    """测试模块导出"""

    def test_terminal_adapter_exported(self):
        """测试 TerminalAdapter 已导出"""
        assert TerminalAdapter is not None

    def test_iterm_adapter_exported(self):
        """测试 iTermAdapter 已导出"""
        assert iTermAdapter is not None

    def test_kitty_adapter_exported(self):
        """测试 KittyAdapter 已导出"""
        assert KittyAdapter is not None

    def test_windows_terminal_adapter_exported(self):
        """测试 WindowsTerminalAdapter 已导出"""
        assert WindowsTerminalAdapter is not None
