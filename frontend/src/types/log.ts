export type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'

export interface Log {
  id: number
  task_id: string
  level: LogLevel
  message: string
  timestamp: string
  // 兼容字段
  created_at?: string
}
