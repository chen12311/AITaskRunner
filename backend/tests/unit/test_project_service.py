"""
Project Service Tests
测试项目服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.project_service import ProjectService
from backend.models.schemas import ProjectCreateRequest, ProjectUpdateRequest


class TestProjectService:
    """测试 ProjectService"""

    @pytest.mark.asyncio
    async def test_create_project(self, test_database):
        """测试创建项目"""
        service = ProjectService(db=test_database)

        request = ProjectCreateRequest(
            name="Test Project",
            directory_path="/tmp/test-project",
            description="A test project"
        )

        project = await service.create_project(request)

        assert project is not None
        assert project.name == "Test Project"
        assert project.directory_path == "/tmp/test-project"
        assert project.description == "A test project"
        assert project.id is not None

    @pytest.mark.asyncio
    async def test_get_project(self, test_database):
        """测试获取项目"""
        service = ProjectService(db=test_database)

        # 先创建一个项目
        request = ProjectCreateRequest(
            name="Test Project",
            directory_path="/tmp/test-project"
        )
        created = await service.create_project(request)

        # 获取项目
        project = await service.get_project(created.id)

        assert project is not None
        assert project.id == created.id
        assert project.name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, test_database):
        """测试获取不存在的项目"""
        service = ProjectService(db=test_database)

        project = await service.get_project("nonexistent_id")

        assert project is None

    @pytest.mark.asyncio
    async def test_get_project_by_directory(self, test_database):
        """测试根据目录路径获取项目"""
        service = ProjectService(db=test_database)

        # 先创建一个项目
        request = ProjectCreateRequest(
            name="Test Project",
            directory_path="/tmp/unique-test-project"
        )
        created = await service.create_project(request)

        # 根据目录获取项目
        project = await service.get_project_by_directory("/tmp/unique-test-project")

        assert project is not None
        assert project.id == created.id

    @pytest.mark.asyncio
    async def test_get_all_projects(self, test_database):
        """测试获取所有项目"""
        service = ProjectService(db=test_database)

        # 创建多个项目
        for i in range(3):
            request = ProjectCreateRequest(
                name=f"Test Project {i}",
                directory_path=f"/tmp/test-project-{i}"
            )
            await service.create_project(request)

        # 获取所有项目
        projects = await service.get_all_projects()

        assert len(projects) >= 3

    @pytest.mark.asyncio
    async def test_update_project(self, test_database):
        """测试更新项目"""
        service = ProjectService(db=test_database)

        # 先创建一个项目
        request = ProjectCreateRequest(
            name="Original Name",
            directory_path="/tmp/test-project"
        )
        created = await service.create_project(request)

        # 更新项目
        update_request = ProjectUpdateRequest(
            name="Updated Name",
            description="Updated description"
        )
        updated = await service.update_project(created.id, update_request)

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, test_database):
        """测试更新不存在的项目"""
        service = ProjectService(db=test_database)

        update_request = ProjectUpdateRequest(name="New Name")
        result = await service.update_project("nonexistent_id", update_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_project_no_changes(self, test_database):
        """测试无更新内容的更新请求"""
        service = ProjectService(db=test_database)

        # 先创建一个项目
        request = ProjectCreateRequest(
            name="Test Project",
            directory_path="/tmp/test-project"
        )
        created = await service.create_project(request)

        # 空更新请求
        update_request = ProjectUpdateRequest()
        result = await service.update_project(created.id, update_request)

        assert result is not None
        assert result.name == "Test Project"

    @pytest.mark.asyncio
    async def test_delete_project(self, test_database):
        """测试删除项目"""
        service = ProjectService(db=test_database)

        # 先创建一个项目
        request = ProjectCreateRequest(
            name="Test Project",
            directory_path="/tmp/test-project-delete"
        )
        created = await service.create_project(request)

        # 删除项目
        success = await service.delete_project(created.id)

        assert success is True

        # 验证项目已删除
        project = await service.get_project(created.id)
        assert project is None

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, test_database):
        """测试删除不存在的项目"""
        service = ProjectService(db=test_database)

        success = await service.delete_project("nonexistent_id")

        assert success is False
