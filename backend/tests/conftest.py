"""
Backend Tests - Shared Fixtures
测试共享配置和 fixtures
"""
import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def temp_db_path() -> AsyncGenerator[str, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)
    # Also cleanup -shm and -wal files
    for ext in ["-shm", "-wal"]:
        wal_file = db_path + ext
        if os.path.exists(wal_file):
            os.unlink(wal_file)


@pytest.fixture(scope="function")
async def test_database(temp_db_path: str):
    """Create a test database instance."""
    from backend.database.models import Database

    db = Database(temp_db_path, pool_size=2)
    await db.initialize()

    # Add missing columns for compatibility
    async with db.get_connection() as conn:
        cursor = await conn.cursor()
        # Add content_en column if not exists
        try:
            await cursor.execute("ALTER TABLE prompt_templates ADD COLUMN content_en TEXT")
        except Exception:
            pass  # Column may already exist

        # Add name_en and description_en columns
        try:
            await cursor.execute("ALTER TABLE prompt_templates ADD COLUMN name_en TEXT")
        except Exception:
            pass

        try:
            await cursor.execute("ALTER TABLE prompt_templates ADD COLUMN description_en TEXT")
        except Exception:
            pass

    yield db
    await db.close()


@pytest.fixture(scope="function")
async def test_app(test_database, monkeypatch):
    """Create a test FastAPI application with test database."""
    from backend.database.shared import reset_shared_database

    # Reset shared database to use test database
    reset_shared_database()

    # Patch get_shared_database to return test database
    def mock_get_shared_database(*args, **kwargs):
        return test_database

    monkeypatch.setattr(
        "backend.database.shared.get_shared_database",
        mock_get_shared_database
    )

    # Also patch the _shared_db directly
    monkeypatch.setattr(
        "backend.database.shared._shared_db",
        test_database
    )

    # Import app module and patch its services
    import backend.app as app_module

    # Create new service instances with test database
    from backend.services.settings_service import SettingsService
    from backend.services.task_service_db import TaskServiceDB
    from backend.services.codex_service import CodexService
    from backend.services.template_service import TemplateService
    from backend.services.project_service import ProjectService

    # Replace service instances in app module
    app_module.settings_service = SettingsService(db=test_database)
    app_module.task_service = TaskServiceDB(db=test_database)
    app_module.template_service = TemplateService(db=test_database)
    app_module.project_service = ProjectService(db=test_database)

    # Initialize codex_service with mocked dependencies
    # Note: CodexService requires special handling due to its dependencies
    app_module.codex_service = CodexService(
        settings_service=app_module.settings_service,
        task_service=app_module.task_service
    )

    yield app_module.app

    # Cleanup
    reset_shared_database()


@pytest.fixture(scope="function")
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def task_service(test_database):
    """Create a TaskServiceDB instance for testing."""
    from backend.services.task_service_db import TaskServiceDB

    service = TaskServiceDB(db=test_database)
    yield service


@pytest.fixture(scope="function")
async def project_service(test_database):
    """Create a ProjectService instance for testing."""
    from backend.services.project_service import ProjectService

    service = ProjectService(db=test_database)
    yield service


@pytest.fixture(scope="function")
async def template_service(test_database):
    """Create a TemplateService instance for testing."""
    from backend.services.template_service import TemplateService

    service = TemplateService(db=test_database)
    yield service


@pytest.fixture(scope="function")
async def settings_service(test_database):
    """Create a SettingsService instance for testing."""
    from backend.services.settings_service import SettingsService

    service = SettingsService(db=test_database)
    yield service


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task data for testing."""
    return {
        "name": "Test Task",
        "description": "A test task description",
        "project_directory": "/tmp/test-project",
        "markdown_document_path": "/tmp/test-project/TODO.md",
        "cli_type": "claude_code"
    }


@pytest.fixture
def sample_project_data() -> dict:
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project description",
        "directory_path": "/tmp/test-project"
    }


@pytest.fixture
def sample_template_data() -> dict:
    """Sample template data for testing."""
    return {
        "name": "test_template",
        "type": "initial_task",
        "locale": "en",
        "content": "Test template content with {{variable}}",
        "description": "A test template"
    }
