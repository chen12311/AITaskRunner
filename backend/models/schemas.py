"""
Pydantic模型 - 简化版本，只存储项目目录和文档路径
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    IN_REVIEWING = "in_reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class CLIType(str, Enum):
    """CLI 类型"""
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    GEMINI = "gemini"


class SessionStatus(str, Enum):
    """会话状态"""
    IDLE = "idle"
    ACTIVE = "active"
    RESTARTING = "restarting"
    ERROR = "error"


class TaskLogModel(BaseModel):
    """任务日志模型"""
    id: int
    task_id: str
    timestamp: str
    level: str
    message: str


class TaskModel(BaseModel):
    """任务模型 - 简化版本"""
    id: str
    project_directory: str
    markdown_document_path: str
    status: str = "pending"
    cli_type: str = "claude_code"
    callback_url: Optional[str] = None
    enable_review: Optional[bool] = None  # None 表示继承全局设置
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    logs: Optional[List[TaskLogModel]] = None


class TaskCreateRequest(BaseModel):
    """创建任务请求 - 简化版本"""
    project_id: str = Field(..., description="项目ID")
    markdown_document_relative_path: str = Field(..., description="Markdown文档相对路径，如 /demo.md")
    cli_type: Optional[str] = Field(None, description="CLI类型: claude_code, codex, gemini")
    callback_url: Optional[str] = Field(None, description="任务完成后的回调URL")
    enable_review: Optional[bool] = Field(None, description="是否启用审查，None 表示继承全局设置")


class TaskUpdateRequest(BaseModel):
    """更新任务请求"""
    project_id: Optional[str] = Field(None, description="项目ID（优先使用）")
    project_directory: Optional[str] = None
    markdown_document_relative_path: Optional[str] = None
    status: Optional[str] = None
    cli_type: Optional[str] = None
    callback_url: Optional[str] = None
    enable_review: Optional[bool] = None


class CodexStatusModel(BaseModel):
    """Codex状态模型"""
    is_running: bool
    session_id: Optional[str] = None
    context_tokens: int = 0
    max_tokens: int = 200000
    context_usage: float = 0.0
    current_task_id: Optional[str] = None


class MonitorStatusResponse(BaseModel):
    """监控状态响应"""
    codex_status: CodexStatusModel
    current_task: Optional[TaskModel] = None
    pending_tasks_count: int


class TaskActionResponse(BaseModel):
    """任务操作响应"""
    success: bool
    message: str
    task_id: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    task_ids: List[str] = Field(..., description="要删除的任务ID列表")


class BatchUpdateStatusRequest(BaseModel):
    """批量修改状态请求"""
    task_ids: List[str] = Field(..., description="要修改的任务ID列表")
    status: str = Field(..., description="目标状态: pending, in_progress, completed, failed")


class BatchActionResponse(BaseModel):
    """批量操作响应"""
    success: bool
    message: str
    affected_count: int = Field(0, description="成功操作的数量")
    failed_ids: List[str] = Field(default_factory=list, description="操作失败的任务ID列表")


class TaskNotificationPayload(BaseModel):
    """任务通知负载 - 发送给回调URL的数据"""
    task_id: str
    status: str  # "completed" or "failed"
    project_directory: str
    markdown_document_path: str
    completed_at: str
    error_message: Optional[str] = None


# ==================== 模板管理 ====================

class TemplateType(str, Enum):
    """模板类型"""
    INITIAL_TASK = "initial_task"
    RESUME_TASK = "resume_task"
    REVIEW = "review"
    CONTINUE_TASK = "continue_task"


class TemplateModel(BaseModel):
    """模板模型"""
    id: str
    name: str
    name_en: Optional[str] = None
    type: str
    content: str
    content_en: Optional[str] = None
    description: Optional[str] = ""
    description_en: Optional[str] = None
    is_default: bool = False
    created_at: str
    updated_at: str


class TemplateCreateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., description="模板名称")
    type: str = Field(..., description="模板类型")
    content: str = Field(..., description="模板内容，支持变量 {project_dir} 和 {doc_path}")
    content_en: Optional[str] = Field(None, description="英文模板内容")
    description: Optional[str] = Field("", description="模板描述")
    is_default: bool = Field(False, description="是否设为默认模板")


class TemplateUpdateRequest(BaseModel):
    """更新模板请求"""
    name: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    content_en: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None


# ==================== 项目管理 ====================

class ProjectModel(BaseModel):
    """项目模型"""
    id: str
    name: str
    directory_path: str
    description: Optional[str] = ""
    created_at: str
    updated_at: str


class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str = Field(..., description="项目名称")
    directory_path: str = Field(..., description="项目目录路径")
    description: Optional[str] = Field("", description="项目描述")


class ProjectUpdateRequest(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    directory_path: Optional[str] = None
    description: Optional[str] = None


class ProjectLaunchRequest(BaseModel):
    """启动项目终端请求"""
    command: Optional[str] = Field(None, description="自定义命令，不填则使用默认CLI")
    mode: str = Field("cli", description="启动模式: cli=启动CLI, terminal=仅打开终端")
    terminal: Optional[str] = Field(None, description="指定终端: iterm, kitty, windows_terminal")
    dangerousMode: bool = Field(False, description="危险模式: 跳过所有确认提示")
