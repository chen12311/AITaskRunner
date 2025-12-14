import client from './client'
import type { Task, CreateTaskData, UpdateTaskData, TaskStatus, BatchActionResponse } from '@/types'

export interface StartTaskResponse {
  success: boolean
  message: string
  task_id: string
  task: Task
}

export interface BatchStartResponse {
  success: boolean
  message: string
  started_count: number
  queued_count: number
  skipped_count: number
  failed_ids: string[]
}

export const taskApi = {
  getAllTasks(): Promise<Task[]> {
    return client.get('/tasks')
  },

  getPendingTasks(): Promise<Task[]> {
    return client.get('/tasks/pending')
  },

  getTask(taskId: string): Promise<Task> {
    return client.get(`/tasks/${taskId}`)
  },

  createTask(data: CreateTaskData): Promise<Task> {
    return client.post('/tasks', data)
  },

  updateTask(taskId: string, data: UpdateTaskData): Promise<Task> {
    return client.put(`/tasks/${taskId}`, data)
  },

  deleteTask(taskId: string): Promise<void> {
    return client.delete(`/tasks/${taskId}`)
  },

  startTask(taskId: string): Promise<StartTaskResponse> {
    return client.post(`/tasks/${taskId}/start`)
  },

  pauseTask(taskId: string): Promise<void> {
    return client.post(`/tasks/${taskId}/pause`)
  },

  restartTask(taskId: string): Promise<void> {
    return client.post(`/tasks/${taskId}/restart`)
  },

  // 批量操作
  batchDelete(taskIds: string[]): Promise<BatchActionResponse> {
    return client.post('/tasks/batch/delete', { task_ids: taskIds })
  },

  batchUpdateStatus(taskIds: string[], status: TaskStatus): Promise<BatchActionResponse> {
    return client.post('/tasks/batch/status', { task_ids: taskIds, status })
  },

  batchStart(): Promise<BatchStartResponse> {
    return client.post('/tasks/batch/start')
  },
}
