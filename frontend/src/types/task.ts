export type TaskStatus = 'pending' | 'in_progress' | 'in_reviewing' | 'completed' | 'failed'
export type CLIType = 'claude_code' | 'codex' | 'aider' | 'cursor'
export type ReviewOption = 'inherit' | 'enabled' | 'disabled'

export interface Task {
  id: string
  project_directory: string
  markdown_document_path: string
  status: TaskStatus
  cli_type?: CLIType
  callback_url?: string | null
  enable_review?: boolean | null
  created_at: string
  updated_at: string
  completed_at?: string | null
  logs?: string | null
  // 计算属性 - 用于显示
  project_name?: string
  doc_path?: string
}

export interface CreateTaskData {
  project_id: string
  markdown_document_relative_path: string
  cli_type?: CLIType
  callback_url?: string
  enable_review?: boolean | null
}

export interface UpdateTaskData {
  project_id?: string
  project_directory?: string
  markdown_document_relative_path?: string
  status?: TaskStatus
  cli_type?: CLIType
  callback_url?: string
  enable_review?: boolean | null
}

export interface Session {
  task_id: string
  status: string
  started_at: string
  pid?: number
}

export interface SessionStats {
  total: number
  active: number
  maxConcurrent: number
  availableSlots: number
}

export interface SessionsAllResponse {
  sessions: Session[]
  total: number
  active: number
  max_concurrent: number
  available_slots: number
}

export interface SessionsActiveResponse {
  sessions: Session[]
  count: number
  max_concurrent: number
}

export type SessionStatusFilter = 'all' | 'running' | 'paused' | 'stopped'

// 批量操作相关类型
export interface BatchDeleteData {
  task_ids: string[]
}

export interface BatchUpdateStatusData {
  task_ids: string[]
  status: TaskStatus
}

export interface BatchActionResponse {
  success: boolean
  message: string
  affected_count: number
  failed_ids: string[]
}
