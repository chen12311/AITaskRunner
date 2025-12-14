"""
CLI Adapter Base Class Tests
测试 CLI 适配器基类
"""
import pytest
from core.cli_adapters.base import CLIAdapter, CLIConfig, CLIStatus, CLIType


class TestCLIType:
    """测试 CLIType 枚举"""

    def test_cli_type_values(self):
        """测试 CLI 类型值"""
        assert CLIType.CLAUDE_CODE.value == "claude_code"
        assert CLIType.CODEX.value == "codex"
        assert CLIType.GEMINI.value == "gemini"

    def test_cli_type_members(self):
        """测试 CLI 类型成员"""
        assert len(CLIType) == 3
        assert CLIType.CLAUDE_CODE in CLIType
        assert CLIType.CODEX in CLIType
        assert CLIType.GEMINI in CLIType


class TestCLIConfig:
    """测试 CLIConfig 数据类"""

    def test_cli_config_creation(self):
        """测试配置创建"""
        config = CLIConfig(
            cli_type=CLIType.CLAUDE_CODE,
            command="claude",
            auto_approve_flag="--auto"
        )
        assert config.cli_type == CLIType.CLAUDE_CODE
        assert config.command == "claude"
        assert config.auto_approve_flag == "--auto"
        assert config.clear_command is None
        assert config.status_command is None
        assert config.resume_flag is None
        assert config.extra_args == []

    def test_cli_config_with_all_fields(self):
        """测试带所有字段的配置"""
        config = CLIConfig(
            cli_type=CLIType.CODEX,
            command="codex",
            auto_approve_flag="--full-auto",
            clear_command="/clear",
            status_command="status",
            resume_flag="--resume",
            extra_args=["--verbose"]
        )
        assert config.clear_command == "/clear"
        assert config.status_command == "status"
        assert config.resume_flag == "--resume"
        assert config.extra_args == ["--verbose"]


class TestCLIStatus:
    """测试 CLIStatus 数据类"""

    def test_cli_status_default(self):
        """测试默认状态"""
        status = CLIStatus(is_running=True)
        assert status.is_running is True
        assert status.session_id is None
        assert status.context_tokens == 0
        assert status.max_tokens == 200000
        assert status.context_usage == 0.0
        assert status.extra_info == {}

    def test_cli_status_with_context(self):
        """测试带上下文信息的状态"""
        status = CLIStatus(
            is_running=True,
            session_id="session_123",
            context_tokens=50000,
            max_tokens=200000,
            context_usage=0.25
        )
        assert status.session_id == "session_123"
        assert status.context_tokens == 50000
        assert status.context_usage == 0.25

    def test_cli_status_not_running(self):
        """测试非运行状态"""
        status = CLIStatus(is_running=False)
        assert status.is_running is False


class TestCLIAdapterBase:
    """测试 CLIAdapter 基类"""

    def test_cli_adapter_is_abstract(self):
        """测试基类是抽象类"""
        with pytest.raises(TypeError):
            CLIAdapter()

    def test_get_env_vars_empty(self):
        """测试空环境变量"""
        # 创建一个具体实现来测试基类方法
        class TestAdapter(CLIAdapter):
            @property
            def name(self): return "Test"
            @property
            def cli_type(self): return CLIType.CLAUDE_CODE
            @property
            def config(self): return None
            def get_start_command(self, project_dir=None): return ""
            def get_clear_session_command(self): return None
            async def get_status(self): return CLIStatus(is_running=False)
            def supports_status_check(self): return False
            def supports_session_resume(self): return False
            def is_available(self): return True

        adapter = TestAdapter()
        env_vars = adapter.get_env_vars()
        assert env_vars == {}

    def test_get_env_vars_with_task_id(self):
        """测试带任务ID的环境变量"""
        class TestAdapter(CLIAdapter):
            @property
            def name(self): return "Test"
            @property
            def cli_type(self): return CLIType.CLAUDE_CODE
            @property
            def config(self): return None
            def get_start_command(self, project_dir=None): return ""
            def get_clear_session_command(self): return None
            async def get_status(self): return CLIStatus(is_running=False)
            def supports_status_check(self): return False
            def supports_session_resume(self): return False
            def is_available(self): return True

        adapter = TestAdapter()
        env_vars = adapter.get_env_vars(task_id="task_123")
        assert env_vars == {"CODEX_TASK_ID": "task_123"}

    def test_get_env_vars_with_api_url(self):
        """测试带API URL的环境变量"""
        class TestAdapter(CLIAdapter):
            @property
            def name(self): return "Test"
            @property
            def cli_type(self): return CLIType.CLAUDE_CODE
            @property
            def config(self): return None
            def get_start_command(self, project_dir=None): return ""
            def get_clear_session_command(self): return None
            async def get_status(self): return CLIStatus(is_running=False)
            def supports_status_check(self): return False
            def supports_session_resume(self): return False
            def is_available(self): return True

        adapter = TestAdapter()
        env_vars = adapter.get_env_vars(api_base_url="http://localhost:8086")
        assert env_vars == {"CODEX_API_BASE_URL": "http://localhost:8086"}

    def test_get_env_vars_full(self):
        """测试完整环境变量"""
        class TestAdapter(CLIAdapter):
            @property
            def name(self): return "Test"
            @property
            def cli_type(self): return CLIType.CLAUDE_CODE
            @property
            def config(self): return None
            def get_start_command(self, project_dir=None): return ""
            def get_clear_session_command(self): return None
            async def get_status(self): return CLIStatus(is_running=False)
            def supports_status_check(self): return False
            def supports_session_resume(self): return False
            def is_available(self): return True

        adapter = TestAdapter()
        env_vars = adapter.get_env_vars(task_id="task_456", api_base_url="http://api.test")
        assert env_vars == {
            "CODEX_TASK_ID": "task_456",
            "CODEX_API_BASE_URL": "http://api.test"
        }

    def test_format_initial_prompt_passthrough(self):
        """测试默认提示词格式化（透传）"""
        class TestAdapter(CLIAdapter):
            @property
            def name(self): return "Test"
            @property
            def cli_type(self): return CLIType.CLAUDE_CODE
            @property
            def config(self): return None
            def get_start_command(self, project_dir=None): return ""
            def get_clear_session_command(self): return None
            async def get_status(self): return CLIStatus(is_running=False)
            def supports_status_check(self): return False
            def supports_session_resume(self): return False
            def is_available(self): return True

        adapter = TestAdapter()
        prompt = "Test prompt with special chars: <>\"'"
        assert adapter.format_initial_prompt(prompt) == prompt
