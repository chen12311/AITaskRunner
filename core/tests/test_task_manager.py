"""
Task Manager Tests
测试任务管理器
"""
import pytest

from core.task_manager import TaskTemplate


class TestTaskTemplateInitialMessage:
    """测试初始任务消息生成"""

    def test_get_initial_task_message_basic(self):
        """测试基本初始任务消息"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert "你是项目经理" in message
        assert "/tmp/project/TODO.md" in message
        assert "项目目录: /tmp/project" in message
        assert "你的职责" in message
        assert "工作流程" in message
        assert "质量要求" in message

    def test_get_initial_task_message_with_task_id(self):
        """测试带任务ID的初始消息"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123"
        )

        assert "task_123" in message
        assert "任务ID: task_123" in message
        assert "/api/tasks/task_123/notify-status" in message

    def test_get_initial_task_message_with_api_url(self):
        """测试自定义 API 地址"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123",
            api_base_url="http://localhost:9000"
        )

        assert "http://localhost:9000" in message
        assert "API地址: http://localhost:9000" in message
        assert "http://localhost:9000/api/tasks/task_123/notify-status" in message

    def test_get_initial_task_message_default_api_url(self):
        """测试默认 API 地址"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123"
        )

        assert "http://127.0.0.1:8086" in message

    def test_get_initial_task_message_contains_status_notification(self):
        """测试消息包含状态通知说明"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123"
        )

        assert "状态通知接口" in message
        assert "session_completed" in message
        assert "completed" in message
        assert "curl -X POST" in message

    def test_get_initial_task_message_contains_workflow(self):
        """测试消息包含工作流程"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert "规划" in message
        assert "执行" in message
        assert "审查" in message
        assert "确认" in message

    def test_get_initial_task_message_contains_quality_requirements(self):
        """测试消息包含质量要求"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert "最佳实践" in message
        assert "错误处理" in message
        assert "测试" in message

    def test_get_initial_task_message_without_task_id(self):
        """测试不带任务ID时不包含任务信息"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        # 不应该有任务信息部分
        assert "任务ID:" not in message


class TestTaskTemplateResumeMessage:
    """测试恢复任务消息生成"""

    def test_get_resume_task_message_basic(self):
        """测试基本恢复消息"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert "会话已重启" in message
        assert "/tmp/project/TODO.md" in message
        assert "项目目录: /tmp/project" in message
        assert "恢复工作" in message

    def test_get_resume_task_message_with_task_id(self):
        """测试带任务ID的恢复消息"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_456"
        )

        assert "task_456" in message
        assert "任务ID: task_456" in message
        assert "/api/tasks/task_456/notify-status" in message

    def test_get_resume_task_message_with_api_url(self):
        """测试自定义 API 地址"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_456",
            api_base_url="http://localhost:9000"
        )

        assert "http://localhost:9000" in message

    def test_get_resume_task_message_contains_recovery_instructions(self):
        """测试消息包含恢复指令"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert "重新阅读文档" in message
        assert "已完成的任务" in message
        assert "未完成的任务" in message
        assert "继续" in message

    def test_get_resume_task_message_contains_status_notification(self):
        """测试恢复消息包含状态通知说明"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_456"
        )

        assert "状态通知接口" in message
        assert "session_completed" in message
        assert "completed" in message
        assert "本次会话是续接" in message

    def test_get_resume_task_message_contains_checklist(self):
        """测试恢复消息包含检查清单"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        assert "检查清单" in message
        assert "确认项目目录结构" in message
        assert "检查已完成的代码" in message

    def test_get_resume_task_message_without_task_id(self):
        """测试不带任务ID时不包含任务信息"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        # 不应该有任务信息部分
        assert "任务ID:" not in message


class TestTaskTemplateEdgeCases:
    """测试边界情况"""

    def test_initial_message_with_special_chars_in_path(self):
        """测试路径包含特殊字符"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project with spaces",
            doc_path="/tmp/project with spaces/TODO.md"
        )

        assert "/tmp/project with spaces" in message
        assert "/tmp/project with spaces/TODO.md" in message

    def test_resume_message_with_special_chars_in_path(self):
        """测试路径包含特殊字符"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/中文项目",
            doc_path="/tmp/中文项目/任务.md"
        )

        assert "/tmp/中文项目" in message
        assert "/tmp/中文项目/任务.md" in message

    def test_initial_message_with_empty_task_id(self):
        """测试空任务ID"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id=""
        )

        # 空字符串应该不产生任务信息块
        assert "任务ID:" not in message

    def test_initial_message_with_none_task_id(self):
        """测试 None 任务ID"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id=None
        )

        assert "任务ID:" not in message

    def test_message_structure_initial(self):
        """测试初始消息结构完整性"""
        message = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123",
            api_base_url="http://localhost:8086"
        )

        # 验证消息包含所有必要部分
        required_sections = [
            "你是项目经理",
            "你的职责",
            "工作流程",
            "质量要求",
            "状态通知",
            "现在开始"
        ]

        for section in required_sections:
            assert section in message, f"Missing section: {section}"

    def test_message_structure_resume(self):
        """测试恢复消息结构完整性"""
        message = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123",
            api_base_url="http://localhost:8086"
        )

        # 验证消息包含所有必要部分
        required_sections = [
            "会话已重启",
            "恢复工作",
            "检查清单",
            "状态通知",
            "现在开始恢复工作"
        ]

        for section in required_sections:
            assert section in message, f"Missing section: {section}"


class TestTaskTemplateConsistency:
    """测试消息一致性"""

    def test_both_messages_contain_doc_reference(self):
        """测试两种消息都包含文档引用"""
        initial_msg = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        resume_msg = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md"
        )

        # 两种消息都应该引用文档
        assert "@/tmp/project/TODO.md" in initial_msg
        assert "@/tmp/project/TODO.md" in resume_msg

    def test_both_messages_contain_status_notification(self):
        """测试两种消息都包含状态通知"""
        initial_msg = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123"
        )

        resume_msg = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123"
        )

        # 两种消息都应该包含状态通知说明
        for msg in [initial_msg, resume_msg]:
            assert "session_completed" in msg
            assert "completed" in msg
            assert "notify-status" in msg

    def test_same_api_url_format(self):
        """测试 API URL 格式一致"""
        api_url = "http://test.example.com:8080"
        task_id = "task_999"

        initial_msg = TaskTemplate.get_initial_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id=task_id,
            api_base_url=api_url
        )

        resume_msg = TaskTemplate.get_resume_task_message(
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id=task_id,
            api_base_url=api_url
        )

        expected_url = f"{api_url}/api/tasks/{task_id}/notify-status"

        assert expected_url in initial_msg
        assert expected_url in resume_msg
