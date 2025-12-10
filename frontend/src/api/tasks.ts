import client from './client'
import type { Task, CreateTaskData, UpdateTaskData } from '@/types'

export interface StartTaskResponse {
  success: boolean
  message: string
  task_id: string
  task: Task
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
}
