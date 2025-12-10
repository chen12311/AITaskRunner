"""
SQLite database models - 异步版本 with 连接池
"""
import aiosqlite
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager


class AsyncConnectionPool:
    """异步连接池管理器 - 支持跨事件循环使用"""

    def __init__(self, db_path: str, pool_size: int = 5):
        """
        初始化连接池

        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool: Optional[asyncio.Queue] = None
        self._initialized = False
        self._lock = None  # 延迟初始化
        self._connections: List[aiosqlite.Connection] = []  # 跟踪所有连接，用于清理

    def _ensure_queue(self):
        """确保队列在当前事件循环中创建"""
        if self._pool is None:
            self._pool = asyncio.Queue(maxsize=self.pool_size)
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化连接池"""
        self._ensure_queue()

        async with self._lock:
            if self._initialized:
                return

            for _ in range(self.pool_size):
                conn = await aiosqlite.connect(self.db_path)
                conn.row_factory = aiosqlite.Row
                # 启用 WAL 模式，提升并发性能
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.commit()
                await self._pool.put(conn)
                self._connections.append(conn)

            self._initialized = True

    async def acquire(self, timeout: float = 30.0) -> aiosqlite.Connection:
        """从连接池获取连接（带超时）"""
        if not self._initialized:
            await self.initialize()

        try:
            return await asyncio.wait_for(self._pool.get(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"获取数据库连接超时 ({timeout}秒)")

    async def release(self, conn: aiosqlite.Connection):
        """归还连接到连接池"""
        if self._pool is not None:
            await self._pool.put(conn)

    async def close_all(self):
        """关闭所有连接"""
        self._initialized = False

        # 关闭所有跟踪的连接
        for conn in self._connections:
            try:
                await conn.close()
            except Exception:
                pass

        self._connections.clear()

        # 清空队列
        if self._pool is not None:
            while not self._pool.empty():
                try:
                    await asyncio.wait_for(self._pool.get(), timeout=0.1)
                except (asyncio.TimeoutError, Exception):
                    break

        self._pool = None
        self._lock = None


class Database:
    """SQLite 异步数据库连接管理器"""

    def __init__(self, db_path: str = "aitaskrunner.db", pool_size: int = 5):
        self.db_path = db_path
        self._pool = AsyncConnectionPool(db_path, pool_size)
        self._init_task = None
        self._init_lock = None

    async def initialize(self):
        """初始化数据库（创建表结构）"""
        # 延迟创建锁，确保在正确的事件循环中
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()

        async with self._init_lock:
            if self._init_task is None:
                self._init_task = asyncio.create_task(self._init_database())
            await self._init_task

    @asynccontextmanager
    async def get_connection(self):
        """异步上下文管理器获取数据库连接"""
        conn = await self._pool.acquire()
        try:
            yield conn
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            raise e
        finally:
            await self._pool.release(conn)

    async def close(self):
        """关闭数据库连接池"""
        await self._pool.close_all()
        self._init_task = None
        self._init_lock = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口 - 自动清理资源"""
        await self.close()

    async def _init_database(self):
        """初始化数据库表"""
        async with self.get_connection() as conn:
            cursor = await conn.cursor()

            # Tasks table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_directory TEXT NOT NULL,
                    markdown_document_path TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    cli_type TEXT DEFAULT 'claude_code',
                    callback_url TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)

            # 数据库迁移：为旧表添加 cli_type 字段
            try:
                await cursor.execute("ALTER TABLE tasks ADD COLUMN cli_type TEXT DEFAULT 'claude_code'")
            except aiosqlite.OperationalError:
                pass  # 字段已存在

            # 数据库迁移：为旧表添加 enable_review 字段（是否启用审查，NULL 表示继承全局设置）
            try:
                await cursor.execute("ALTER TABLE tasks ADD COLUMN enable_review INTEGER DEFAULT NULL")
            except aiosqlite.OperationalError:
                pass  # 字段已存在

            # Task execution logs
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)

            # Prompt templates table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Projects table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    directory_path TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # System settings table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create indexes
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks(status)
            """)

            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_logs_task_id
                ON task_logs(task_id)
            """)

            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompt_templates_type
                ON prompt_templates(type)
            """)

            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_directory
                ON projects(directory_path)
            """)

            # 优化5.1: 为 task_logs.timestamp 添加索引（加速日志排序）
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_logs_timestamp
                ON task_logs(timestamp DESC)
            """)

            # 优化5.2: 为 tasks.updated_at 添加索引（支持按更新时间排序）
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_updated_at
                ON tasks(updated_at DESC)
            """)

            # 优化5.3: 添加复合索引 (task_id, timestamp) 优化日志查询
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_logs_task_timestamp
                ON task_logs(task_id, timestamp DESC)
            """)


class TaskDAO:
    """Data Access Object for tasks - 异步版本"""

    def __init__(self, db: Database):
        self.db = db

    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            now = datetime.now().isoformat()
            task_id = task_data.get('id', f"task_{uuid.uuid4().hex[:12]}")

            # enable_review: None 表示继承全局设置，True/False 表示覆盖
            enable_review = task_data.get('enable_review')
            enable_review_value = None if enable_review is None else (1 if enable_review else 0)

            await cursor.execute("""
                INSERT INTO tasks (
                    id, project_directory, markdown_document_path,
                    status, cli_type, callback_url, enable_review, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task_data['project_directory'],
                task_data['markdown_document_path'],
                task_data.get('status', 'pending'),
                task_data.get('cli_type', 'claude_code'),
                task_data.get('callback_url'),
                enable_review_value,
                now,
                now
            ))

            return task_id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID (with logs)"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = await cursor.fetchone()

            if not row:
                return None

            task = dict(row)

            # Get recent logs
            await cursor.execute("""
                SELECT * FROM task_logs
                WHERE task_id = ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (task_id,))
            rows = await cursor.fetchall()
            task['logs'] = [dict(row) for row in rows]

            return task

    async def get_task_basic(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID without logs (optimized for list queries)"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks with pending or in_progress status"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("""
                SELECT * FROM tasks
                WHERE status IN ('pending', 'in_progress')
                ORDER BY created_at ASC
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            set_clauses = []
            values = []

            allowed_fields = ['project_directory', 'markdown_document_path', 'status', 'cli_type', 'callback_url', 'completed_at', 'enable_review']

            for field in allowed_fields:
                if field in updates:
                    set_clauses.append(f"{field} = ?")
                    values.append(updates[field])

            if not set_clauses:
                return False

            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(task_id)

            query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
            await cursor.execute(query, values)

            return cursor.rowcount > 0

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    async def add_log(self, task_id: str, level: str, message: str) -> int:
        """Add a log entry for a task"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            await cursor.execute("""
                INSERT INTO task_logs (
                    task_id, timestamp, level, message
                ) VALUES (?, ?, ?, ?)
            """, (
                task_id,
                datetime.now().isoformat(),
                level,
                message
            ))

            return cursor.lastrowid

    async def add_logs_batch(self, logs: List[Dict[str, Any]]) -> int:
        """
        优化4.3: 批量写入日志

        Args:
            logs: 日志列表，每条日志包含 task_id, level, message, timestamp(可选)

        Returns:
            写入的日志数量
        """
        if not logs:
            return 0

        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            now = datetime.now().isoformat()

            # 准备批量插入数据
            values = [
                (
                    log['task_id'],
                    log.get('timestamp', now),
                    log['level'],
                    log['message']
                )
                for log in logs
            ]

            await cursor.executemany("""
                INSERT INTO task_logs (task_id, timestamp, level, message)
                VALUES (?, ?, ?, ?)
            """, values)

            return len(logs)

    async def get_logs(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a task"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("""
                SELECT * FROM task_logs
                WHERE task_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (task_id, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


class TemplateDAO:
    """Data Access Object for prompt templates - 异步版本"""

    def __init__(self, db: Database):
        self.db = db

    async def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new template"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            now = datetime.now().isoformat()
            template_id = template_data.get('id', f"tpl_{uuid.uuid4().hex[:12]}")

            await cursor.execute("""
                INSERT INTO prompt_templates (
                    id, name, type, content, content_en, description, is_default,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template_id,
                template_data['name'],
                template_data['type'],
                template_data['content'],
                template_data.get('content_en'),
                template_data.get('description', ''),
                template_data.get('is_default', 0),
                now,
                now
            ))

            return template_id

    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM prompt_templates WHERE id = ?", (template_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_template_by_type(self, template_type: str, use_default: bool = True) -> Optional[Dict[str, Any]]:
        """Get template by type, optionally only default"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            if use_default:
                await cursor.execute("""
                    SELECT * FROM prompt_templates
                    WHERE type = ? AND is_default = 1
                    LIMIT 1
                """, (template_type,))
            else:
                await cursor.execute("""
                    SELECT * FROM prompt_templates
                    WHERE type = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (template_type,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM prompt_templates ORDER BY type, name")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_templates_by_type(self, template_type: str) -> List[Dict[str, Any]]:
        """Get all templates of a specific type"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("""
                SELECT * FROM prompt_templates
                WHERE type = ?
                ORDER BY is_default DESC, name
            """, (template_type,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update a template"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            set_clauses = []
            values = []

            allowed_fields = ['name', 'type', 'content', 'content_en', 'description', 'is_default']

            for field in allowed_fields:
                if field in updates:
                    set_clauses.append(f"{field} = ?")
                    values.append(updates[field])

            if not set_clauses:
                return False

            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(template_id)

            query = f"UPDATE prompt_templates SET {', '.join(set_clauses)} WHERE id = ?"
            await cursor.execute(query, values)

            return cursor.rowcount > 0

    async def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM prompt_templates WHERE id = ?", (template_id,))
            return cursor.rowcount > 0

    async def set_default_template(self, template_id: str) -> bool:
        """Set a template as default for its type"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            # Get template type
            await cursor.execute("SELECT type FROM prompt_templates WHERE id = ?", (template_id,))
            row = await cursor.fetchone()
            if not row:
                return False

            template_type = row['type']

            # Clear other defaults of same type
            await cursor.execute("""
                UPDATE prompt_templates
                SET is_default = 0
                WHERE type = ?
            """, (template_type,))

            # Set this one as default
            await cursor.execute("""
                UPDATE prompt_templates
                SET is_default = 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), template_id))

            return cursor.rowcount > 0


class ProjectDAO:
    """Data Access Object for projects - 异步版本"""

    def __init__(self, db: Database):
        self.db = db

    async def create_project(self, project_data: Dict[str, Any]) -> str:
        """Create a new project"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            now = datetime.now().isoformat()
            project_id = project_data.get('id', f"proj_{uuid.uuid4().hex[:12]}")

            await cursor.execute("""
                INSERT INTO projects (
                    id, name, directory_path, description, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                project_data['name'],
                project_data['directory_path'],
                project_data.get('description', ''),
                now,
                now
            ))

            return project_id

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_project_by_directory(self, directory_path: str) -> Optional[Dict[str, Any]]:
        """Get a project by directory path"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM projects WHERE directory_path = ?", (directory_path,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM projects ORDER BY name")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update a project"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            set_clauses = []
            values = []

            allowed_fields = ['name', 'directory_path', 'description']

            for field in allowed_fields:
                if field in updates:
                    set_clauses.append(f"{field} = ?")
                    values.append(updates[field])

            if not set_clauses:
                return False

            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(project_id)

            query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ?"
            await cursor.execute(query, values)

            return cursor.rowcount > 0

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0


class SettingsDAO:
    """Data Access Object for system settings - 异步版本"""

    def __init__(self, db: Database):
        self.db = db

    async def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row['value'] if row else None

    async def get_all_settings(self) -> Dict[str, str]:
        """Get all settings"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT key, value FROM system_settings")
            rows = await cursor.fetchall()
            return {row['key']: row['value'] for row in rows}

    async def set_setting(self, key: str, value: str, description: str = "") -> bool:
        """Set a setting value"""
        async with self.db.get_connection() as conn:
            cursor = await conn.cursor()

            now = datetime.now().isoformat()

            # 使用 INSERT OR REPLACE 语法
            await cursor.execute("""
                INSERT OR REPLACE INTO system_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, value, description, now))

            return True
