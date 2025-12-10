"""
优化6.1-6.3: 共享数据库实例 - 所有服务使用同一个连接池
"""
from pathlib import Path
from typing import Optional
from backend.database.models import Database

# 共享数据库实例
_shared_db: Optional[Database] = None


def get_shared_database(db_path: str = None, pool_size: int = 10) -> Database:
    """
    获取共享的数据库实例（单例模式）

    Args:
        db_path: 数据库文件路径，默认为项目根目录下的 aitaskrunner.db
        pool_size: 连接池大小，默认10（优化后共享连接池）

    Returns:
        Database: 共享的数据库实例
    """
    global _shared_db

    if _shared_db is None:
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "aitaskrunner.db")
        _shared_db = Database(db_path, pool_size=pool_size)

    return _shared_db


async def close_shared_database():
    """关闭共享数据库连接"""
    global _shared_db

    if _shared_db is not None:
        await _shared_db.close()
        _shared_db = None


def reset_shared_database():
    """重置共享数据库实例（用于测试）"""
    global _shared_db
    _shared_db = None
