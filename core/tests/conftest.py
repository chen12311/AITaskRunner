"""
Core Tests - Shared Fixtures
核心模块测试共享配置
"""
import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_shutil_which(mocker):
    """Mock shutil.which for testing CLI availability."""
    return mocker.patch("shutil.which")


@pytest.fixture
def mock_path_exists(mocker):
    """Mock Path.exists for testing file existence."""
    return mocker.patch("pathlib.Path.exists")


@pytest.fixture
def mock_asyncio_subprocess(mocker):
    """Mock asyncio.create_subprocess_exec for testing subprocess calls."""
    return mocker.patch("asyncio.create_subprocess_exec")
