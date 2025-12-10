import client from './client'
import type { Log } from '@/types'

// 后端返回格式: {logs: [...], total: number}
interface LogsResponse {
  logs: Log[]
  total: number
}

export const logApi = {
  getTaskLogs(taskId: string, limit: number = 100): Promise<LogsResponse> {
    return client.get(`/tasks/${taskId}/logs`, { params: { limit } })
  },
}
