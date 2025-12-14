"""
Template Service Tests
测试模板服务
"""
import pytest

from backend.services.template_service import TemplateService
from backend.models.schemas import TemplateCreateRequest, TemplateUpdateRequest


class TestTemplateService:
    """测试 TemplateService"""

    @pytest.mark.asyncio
    async def test_initialize_default_templates(self, test_database):
        """测试初始化创建默认模板"""
        service = TemplateService(db=test_database)
        await service.initialize()

        templates = await service.get_all_templates()

        # 应该有4个默认模板
        assert len(templates) >= 4

        # 检查类型
        types = {t.type for t in templates}
        assert "initial_task" in types
        assert "resume_task" in types
        assert "review" in types
        assert "continue_task" in types

    @pytest.mark.asyncio
    async def test_get_all_templates(self, test_database):
        """测试获取所有模板"""
        service = TemplateService(db=test_database)

        templates = await service.get_all_templates()

        assert isinstance(templates, list)
        assert len(templates) >= 4

    @pytest.mark.asyncio
    async def test_get_template(self, test_database):
        """测试获取单个模板"""
        service = TemplateService(db=test_database)

        # 获取默认的初始任务模板
        template = await service.get_template("tpl_initial_default")

        assert template is not None
        assert template.type == "initial_task"
        assert template.is_default is True

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, test_database):
        """测试获取不存在的模板"""
        service = TemplateService(db=test_database)

        template = await service.get_template("nonexistent")

        assert template is None

    @pytest.mark.asyncio
    async def test_get_templates_by_type(self, test_database):
        """测试按类型获取模板"""
        service = TemplateService(db=test_database)

        templates = await service.get_templates_by_type("initial_task")

        assert len(templates) >= 1
        for t in templates:
            assert t.type == "initial_task"

    @pytest.mark.asyncio
    async def test_get_default_template(self, test_database):
        """测试获取默认模板"""
        service = TemplateService(db=test_database)

        template = await service.get_default_template("initial_task")

        assert template is not None
        assert template.type == "initial_task"
        assert template.is_default is True

    @pytest.mark.asyncio
    async def test_create_template(self, test_database):
        """测试创建模板"""
        service = TemplateService(db=test_database)

        request = TemplateCreateRequest(
            name="Test Template",
            type="custom",
            content="Hello {{name}}!",
            description="A test template"
        )

        template = await service.create_template(request)

        assert template is not None
        assert template.name == "Test Template"
        assert template.type == "custom"
        assert template.content == "Hello {{name}}!"

    @pytest.mark.asyncio
    async def test_create_template_as_default(self, test_database):
        """测试创建默认模板"""
        service = TemplateService(db=test_database)

        # 先创建一个非默认模板
        request1 = TemplateCreateRequest(
            name="First Template",
            type="new_type",
            content="First",
            is_default=True
        )
        first = await service.create_template(request1)

        # 再创建一个默认模板（应该清除第一个的默认状态）
        request2 = TemplateCreateRequest(
            name="Second Template",
            type="new_type",
            content="Second",
            is_default=True
        )
        second = await service.create_template(request2)

        # 获取第一个模板，应该不再是默认
        updated_first = await service.get_template(first.id)
        assert updated_first.is_default is False

        # 第二个应该是默认
        assert second.is_default is True

    @pytest.mark.asyncio
    async def test_update_template(self, test_database):
        """测试更新模板"""
        service = TemplateService(db=test_database)

        # 先创建一个模板
        request = TemplateCreateRequest(
            name="Original",
            type="test",
            content="Original content"
        )
        created = await service.create_template(request)

        # 更新模板
        update_request = TemplateUpdateRequest(
            name="Updated",
            content="Updated content"
        )
        updated = await service.update_template(created.id, update_request)

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.content == "Updated content"

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, test_database):
        """测试更新不存在的模板"""
        service = TemplateService(db=test_database)

        update_request = TemplateUpdateRequest(name="New Name")
        result = await service.update_template("nonexistent", update_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_template(self, test_database):
        """测试删除模板"""
        service = TemplateService(db=test_database)

        # 先创建一个模板
        request = TemplateCreateRequest(
            name="To Delete",
            type="delete_test",
            content="Delete me"
        )
        created = await service.create_template(request)

        # 删除模板
        success = await service.delete_template(created.id)

        assert success is True

        # 验证已删除
        template = await service.get_template(created.id)
        assert template is None

    @pytest.mark.asyncio
    async def test_set_default_template(self, test_database):
        """测试设置默认模板"""
        service = TemplateService(db=test_database)

        # 创建两个模板
        request1 = TemplateCreateRequest(
            name="Template 1",
            type="default_test",
            content="Content 1",
            is_default=True
        )
        tpl1 = await service.create_template(request1)

        request2 = TemplateCreateRequest(
            name="Template 2",
            type="default_test",
            content="Content 2"
        )
        tpl2 = await service.create_template(request2)

        # 设置第二个为默认
        success = await service.set_default_template(tpl2.id)
        assert success is True

        # 验证
        default = await service.get_default_template("default_test")
        assert default.id == tpl2.id


class TestTemplateServiceRender:
    """测试模板渲染功能"""

    @pytest.mark.asyncio
    async def test_render_template(self, test_database):
        """测试渲染模板"""
        service = TemplateService(db=test_database)

        # 渲染初始任务模板
        content = await service.render_template(
            "initial_task",
            project_dir="/tmp/project",
            doc_path="/tmp/project/TODO.md",
            task_id="task_123",
            api_base_url="http://localhost:8086"
        )

        assert "/tmp/project" in content
        assert "/tmp/project/TODO.md" in content
        assert "task_123" in content
        assert "http://localhost:8086" in content

    @pytest.mark.asyncio
    async def test_render_template_async(self, test_database):
        """测试异步渲染模板"""
        service = TemplateService(db=test_database)

        content = await service.render_template_async(
            "resume_task",
            locale="zh",
            project_dir="/home/user/project",
            doc_path="/home/user/project/PLAN.md",
            task_id="task_456",
            api_base_url="http://api.example.com"
        )

        assert "/home/user/project" in content
        assert "task_456" in content

    @pytest.mark.asyncio
    async def test_render_template_not_found(self, test_database):
        """测试渲染不存在的模板类型"""
        service = TemplateService(db=test_database)

        with pytest.raises(ValueError) as exc_info:
            await service.render_template("nonexistent_type")

        assert "No default template found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_render_template_with_english(self, test_database):
        """测试英文模板渲染"""
        service = TemplateService(db=test_database)

        # 创建带英文内容的模板
        request = TemplateCreateRequest(
            name="Bilingual",
            type="bilingual_test",
            content="中文内容: {name}",
            content_en="English content: {name}",
            is_default=True
        )
        await service.create_template(request)

        # 渲染中文
        zh_content = await service.render_template_async(
            "bilingual_test",
            locale="zh",
            name="测试"
        )
        assert "中文内容: 测试" in zh_content

        # 渲染英文
        en_content = await service.render_template_async(
            "bilingual_test",
            locale="en",
            name="Test"
        )
        assert "English content: Test" in en_content
