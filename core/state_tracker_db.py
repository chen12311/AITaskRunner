"""
State Tracker using SQLite database
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from backend.database.models import Database, TaskStateDAO, SessionStateDAO


class TaskStatus(Enum):
    """Task status enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(Enum):
    """Session status enum"""
    IDLE = "idle"
    ACTIVE = "active"
    RESTARTING = "restarting"
    ERROR = "error"


class StateTrackerDB:
    """State tracker using SQLite database"""

    def __init__(self, db_path: str = "aitaskrunner.db"):
        """
        Initialize state tracker with database

        Args:
            db_path: Database file path
        """
        self.db = Database(db_path)
        self.task_state_dao = TaskStateDAO(self.db)
        self.session_state_dao = SessionStateDAO(self.db)

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

        # Set timestamps based on status
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

        # Count by status
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
