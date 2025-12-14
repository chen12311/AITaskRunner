"""
Terminal Adapter Base Class Tests
测试终端适配器基类
"""
import pytest
from core.terminal_adapters.base import TerminalAdapter, TerminalSession


class TestTerminalSession:
    """测试 TerminalSession 数据类"""

    def test_session_creation_minimal(self):
        """测试最小会话创建"""
        session = TerminalSession(session_id="sess_123")
        assert session.session_id == "sess_123"
        assert session.window_id is None
        assert session.socket_path is None

    def test_session_creation_full(self):
        """测试完整会话创建"""
        session = TerminalSession(
            session_id="sess_456",
            window_id="win_789",
            socket_path="/tmp/kitty-123"
        )
        assert session.session_id == "sess_456"
        assert session.window_id == "win_789"
        assert session.socket_path == "/tmp/kitty-123"


class TestTerminalAdapterBase:
    """测试 TerminalAdapter 基类"""

    def test_terminal_adapter_is_abstract(self):
        """测试基类是抽象类"""
        with pytest.raises(TypeError):
            TerminalAdapter()

    def test_has_active_session_false(self):
        """测试无活跃会话"""
        class TestAdapter(TerminalAdapter):
            @property
            def name(self): return "Test"
            async def create_window(self, project_dir, command, task_id=None, api_base_url=None): return None
            async def send_text(self, text, press_enter=True): return False
            async def close_window(self): return True
            def is_available(self): return True

        adapter = TestAdapter()
        assert adapter.has_active_session() is False

    def test_has_active_session_true(self):
        """测试有活跃会话"""
        class TestAdapter(TerminalAdapter):
            @property
            def name(self): return "Test"
            async def create_window(self, project_dir, command, task_id=None, api_base_url=None): return None
            async def send_text(self, text, press_enter=True): return False
            async def close_window(self): return True
            def is_available(self): return True

        adapter = TestAdapter()
        adapter.current_session = TerminalSession(session_id="test")
        assert adapter.has_active_session() is True

    def test_is_window_alive_default(self):
        """测试默认窗口存活检查"""
        class TestAdapter(TerminalAdapter):
            @property
            def name(self): return "Test"
            async def create_window(self, project_dir, command, task_id=None, api_base_url=None): return None
            async def send_text(self, text, press_enter=True): return False
            async def close_window(self): return True
            def is_available(self): return True

        adapter = TestAdapter()
        assert adapter.is_window_alive() is False

        adapter.current_session = TerminalSession(session_id="test")
        assert adapter.is_window_alive() is True

    def test_clear_session(self):
        """测试清除会话"""
        class TestAdapter(TerminalAdapter):
            @property
            def name(self): return "Test"
            async def create_window(self, project_dir, command, task_id=None, api_base_url=None): return None
            async def send_text(self, text, press_enter=True): return False
            async def close_window(self): return True
            def is_available(self): return True

        adapter = TestAdapter()
        adapter.current_session = TerminalSession(session_id="test")
        assert adapter.has_active_session() is True

        adapter.clear_session()
        assert adapter.current_session is None
        assert adapter.has_active_session() is False
