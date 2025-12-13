"""
State Tracker using SQLite database
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(Enum):
    """会话状态枚举"""
    IDLE = "idle"
    ACTIVE = "active"
    RESTARTING = "restarting"
    ERROR = "error"


class TaskStateDAO:
    """Lightweight DAO for task state tracking (sync, SQLite)"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False
        self._ensure_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        if self._initialized:
            return
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_states (
                    task_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    started_at TEXT,
                    completed_at TEXT,
                    last_updated TEXT,
                    error_message TEXT,
                    restart_count INTEGER DEFAULT 0
                )
                """
            )
        self._initialized = True

    def update_task_state(self, task_id: str, updates: Dict[str, Any]):
        """Insert or update a task state record"""
        now = datetime.now().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM task_states WHERE task_id = ?", (task_id,)
            ).fetchone()

            base = {
                "task_id": task_id,
                "status": TaskStatus.PENDING.value,
                "progress": 0.0,
                "started_at": None,
                "completed_at": None,
                "last_updated": now,
                "error_message": None,
                "restart_count": 0,
            }

            if row:
                base.update(dict(row))

            base.update(updates)
            base["last_updated"] = now

            conn.execute(
                """
                INSERT OR REPLACE INTO task_states (
                    task_id, status, progress, started_at, completed_at,
                    last_updated, error_message, restart_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    base["task_id"],
                    base["status"],
                    base.get("progress", 0.0),
                    base.get("started_at"),
                    base.get("completed_at"),
                    base["last_updated"],
                    base.get("error_message"),
                    base.get("restart_count", 0),
                ),
            )

    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task state"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM task_states WHERE task_id = ?", (task_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_states(self) -> List[Dict[str, Any]]:
        """Get all task states"""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM task_states").fetchall()
            return [dict(row) for row in rows]


class SessionStateDAO:
    """Lightweight DAO for session state tracking (sync, SQLite)"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False
        self._ensure_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        if self._initialized:
            return
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_states (
                    session_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    current_task TEXT,
                    context_usage TEXT,
                    last_updated TEXT
                )
                """
            )
        self._initialized = True

    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Insert or update a session record"""
        now = datetime.now().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM session_states WHERE session_id = ?", (session_id,)
            ).fetchone()

            base = {
                "session_id": session_id,
                "status": SessionStatus.IDLE.value,
                "current_task": None,
                "context_usage": None,
                "last_updated": now,
            }

            if row:
                base.update(dict(row))

            base.update(updates)
            base["last_updated"] = now

            conn.execute(
                """
                INSERT OR REPLACE INTO session_states (
                    session_id, status, current_task, context_usage, last_updated
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    base["session_id"],
                    base["status"],
                    base.get("current_task"),
                    json.dumps(base.get("context_usage"))
                    if base.get("context_usage") is not None
                    else None,
                    base["last_updated"],
                ),
            )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a single session state"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM session_states WHERE session_id = ?", (session_id,)
            ).fetchone()

            if not row:
                return None

            data = dict(row)
            if data.get("context_usage"):
                try:
                    data["context_usage"] = json.loads(data["context_usage"])
                except (TypeError, json.JSONDecodeError):
                    data["context_usage"] = None
            return data


class StateTrackerDB:
    """使用SQLite数据库的状态追踪器"""

    def __init__(self, db_path: str = "aitaskrunner.db"):
        """
        Initialize state tracker with database

        Args:
            db_path: Database file path
        """
        db_path = str(Path(db_path))
        self.task_state_dao = TaskStateDAO(db_path)
        self.session_state_dao = SessionStateDAO(db_path)

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """
        Update task status

        Args:
            task_id: Task ID
            status: New status
            progress: Progress (0.0 - 1.0)
            error_message: Error message if failed
        """
        updates = {
            'status': status.value
        }

        if progress is not None:
            updates['progress'] = progress

        if error_message is not None:
            updates['error_message'] = error_message

        # 根据状态设置时间戳
        now = datetime.now().isoformat()
        if status == TaskStatus.IN_PROGRESS:
            updates['started_at'] = now
        elif status == TaskStatus.COMPLETED:
            updates['completed_at'] = now
            updates['progress'] = 1.0

        self.task_state_dao.update_task_state(task_id, updates)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status

        Args:
            task_id: Task ID

        Returns:
            Task state dict or None
        """
        return self.task_state_dao.get_task_state(task_id)

    def increment_restart_count(self, task_id: str):
        """
        Increment task restart count

        Args:
            task_id: Task ID
        """
        state = self.task_state_dao.get_task_state(task_id)
        if state:
            restart_count = state.get('restart_count', 0) + 1
            self.task_state_dao.update_task_state(task_id, {
                'restart_count': restart_count
            })

    def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        current_task: Optional[str] = None,
        context_usage: Optional[Dict[str, Any]] = None
    ):
        """
        Update session status

        Args:
            session_id: Session ID
            status: New status
            current_task: Current task ID
            context_usage: Context usage info
        """
        updates = {
            'status': status.value
        }

        if current_task is not None:
            updates['current_task'] = current_task

        if context_usage is not None:
            updates['context_usage'] = context_usage

        self.session_state_dao.update_session(session_id, updates)

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session status

        Args:
            session_id: Session ID

        Returns:
            Session state dict or None
        """
        return self.session_state_dao.get_session(session_id)

    def get_all_task_states(self) -> List[Dict[str, Any]]:
        """
        Get all task states

        Returns:
            List of task state dicts
        """
        return self.task_state_dao.get_all_states()

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Get pending tasks

        Returns:
            List of pending task states
        """
        all_states = self.task_state_dao.get_all_states()
        return [
            state for state in all_states
            if state['status'] == TaskStatus.PENDING.value
        ]

    def get_in_progress_tasks(self) -> List[Dict[str, Any]]:
        """
        Get in-progress tasks

        Returns:
            List of in-progress task states
        """
        all_states = self.task_state_dao.get_all_states()
        return [
            state for state in all_states
            if state['status'] == TaskStatus.IN_PROGRESS.value
        ]

    def export_report(self) -> Dict[str, Any]:
        """
        Export status report

        Returns:
            Status report dict
        """
        all_states = self.task_state_dao.get_all_states()

        # 按状态统计
        status_counts = {
            'pending': 0,
            'in_progress': 0,
            'paused': 0,
            'completed': 0,
            'failed': 0
        }

        total_progress = 0.0
        restart_counts = []

        for state in all_states:
            status = state['status']
            if status in status_counts:
                status_counts[status] += 1

            total_progress += state.get('progress', 0.0)
            restart_counts.append(state.get('restart_count', 0))

        avg_progress = total_progress / len(all_states) if all_states else 0.0
        avg_restarts = sum(restart_counts) / len(restart_counts) if restart_counts else 0.0

        return {
            'timestamp': datetime.now().isoformat(),
            'total_tasks': len(all_states),
            'status_counts': status_counts,
            'average_progress': avg_progress,
            'average_restarts': avg_restarts,
            'tasks': all_states
        }
