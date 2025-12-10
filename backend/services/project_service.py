"""
项目管理服务 - 异步版本
"""
from typing import List, Optional
from backend.database.models import Database, ProjectDAO
from backend.models.schemas import ProjectModel, ProjectCreateRequest, ProjectUpdateRequest


class ProjectService:
    """项目管理服务 - 异步版本"""

    def __init__(self, db_path: str = "aitaskrunner.db", db: Database = None):
        """
        初始化项目服务

        优化6.2: 支持注入共享数据库实例

        Args:
            db_path: 数据库文件路径（如果 db 为 None 时使用）
            db: 共享的数据库实例（优先使用）
        """
        if db is not None:
            self.db = db
        else:
            self.db = Database(db_path)
        self.project_dao = ProjectDAO(self.db)
        self._initialized = False

    async def initialize(self):
        """初始化数据库"""
        if not self._initialized:
            await self.db.initialize()
            self._initialized = True

    async def create_project(self, request: ProjectCreateRequest) -> ProjectModel:
        """创建项目"""
        await self.initialize()
        project_data = {
            "name": request.name,
            "directory_path": request.directory_path,
            "description": request.description or ""
        }
        project_id = await self.project_dao.create_project(project_data)
        return await self.get_project(project_id)

    async def get_project(self, project_id: str) -> Optional[ProjectModel]:
        """获取项目"""
        await self.initialize()
        project = await self.project_dao.get_project(project_id)
        if not project:
            return None
        return ProjectModel(**project)

    async def get_project_by_directory(self, directory_path: str) -> Optional[ProjectModel]:
        """根据目录路径获取项目"""
        await self.initialize()
        project = await self.project_dao.get_project_by_directory(directory_path)
        if not project:
            return None
        return ProjectModel(**project)

    async def get_all_projects(self) -> List[ProjectModel]:
        """获取所有项目"""
        await self.initialize()
        projects = await self.project_dao.get_all_projects()
        return [ProjectModel(**p) for p in projects]

    async def update_project(self, project_id: str, request: ProjectUpdateRequest) -> Optional[ProjectModel]:
        """更新项目"""
        await self.initialize()
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.directory_path is not None:
            updates["directory_path"] = request.directory_path
        if request.description is not None:
            updates["description"] = request.description

        if not updates:
            return await self.get_project(project_id)

        success = await self.project_dao.update_project(project_id, updates)
        if not success:
            return None
        return await self.get_project(project_id)

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        await self.initialize()
        return await self.project_dao.delete_project(project_id)
