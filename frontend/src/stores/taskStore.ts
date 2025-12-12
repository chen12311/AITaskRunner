import { create } from 'zustand'
import { taskApi } from '@/api'
import { extractData, isSuccess } from '@/api/client'
import type { Task, TaskStatus } from '@/types/task'

interface TaskState {
  tasks: Task[]
  loading: boolean
  error: string | null

  fetchTasks: () => Promise<void>
  setTasks: (tasks: Task[]) => void  // 优化1.1: 直接设置任务列表（用于批量初始化）
  createTask: (data: Parameters<typeof taskApi.createTask>[0]) => Promise<void>
  updateTask: (taskId: string, data: Parameters<typeof taskApi.updateTask>[1]) => Promise<void>
  deleteTask: (taskId: string) => Promise<void>
  startTask: (taskId: string) => Promise<void>
  setFilter: (status: TaskStatus | 'all') => void
  filter: TaskStatus | 'all'
}

// 为任务添加显示属性的辅助函数
const enrichTask = (task: Task): Task => ({
  ...task,
  project_name: task.project_directory?.split('/').pop() || task.project_directory,
  doc_path: task.markdown_document_path?.split('/').pop() || task.markdown_document_path,
})

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  loading: false,
  error: null,
  filter: 'all',

  fetchTasks: async () => {
    set({ loading: true, error: null })
    try {
      const response = await taskApi.getAllTasks()
      const tasks = extractData<Task[]>(response).map(enrichTask)
      set({ tasks })
    } catch (error) {
      set({ error: (error as Error).message })
    } finally {
      set({ loading: false })
    }
  },

  // 优化1.1: 直接设置任务列表（用于批量初始化，避免额外请求）
  setTasks: (tasks: Task[]) => {
    set({ tasks: tasks.map(enrichTask) })
  },

  // 优化2.1: createTask - 使用返回的任务数据直接 push，避免全量刷新
  createTask: async (data) => {
    set({ loading: true, error: null })
    try {
      const response = await taskApi.createTask(data)
      const newTask = extractData<Task>(response)
      if (newTask) {
        // 直接将新任务添加到列表开头（按创建时间倒序）
        set((state) => ({
          tasks: [enrichTask(newTask), ...state.tasks]
        }))
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },

  // 优化2.3: updateTask - 使用返回的任务数据直接替换，避免全量刷新
  updateTask: async (taskId, data) => {
    set({ loading: true, error: null })
    try {
      const response = await taskApi.updateTask(taskId, data)
      const updatedTask = extractData<Task>(response)
      if (updatedTask) {
        // 直接替换对应的任务
        set((state) => ({
          tasks: state.tasks.map((task) =>
            task.id === taskId ? enrichTask(updatedTask) : task
          )
        }))
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },

  // 优化2.2 + 2.5: deleteTask - 乐观更新（先删除UI，失败再回滚）
  deleteTask: async (taskId) => {
    // 保存当前状态用于回滚
    const previousTasks = get().tasks

    // 乐观更新：立即从UI移除
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== taskId)
    }))

    try {
      const response = await taskApi.deleteTask(taskId)
      if (!isSuccess(response)) {
        // API 返回失败，回滚
        set({ tasks: previousTasks, error: 'Delete failed' })
      }
    } catch (error) {
      // 请求失败，回滚到之前的状态
      set({ tasks: previousTasks, error: (error as Error).message })
      throw error
    }
  },

  // 优化2.4 + 2.5: startTask - 乐观更新（先更新状态为 in_progress，失败再回滚）
  startTask: async (taskId) => {
    // 保存当前状态用于回滚
    const previousTasks = get().tasks

    // 乐观更新：立即将状态改为 in_progress
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId ? { ...task, status: 'in_progress' as TaskStatus } : task
      )
    }))

    try {
      const response = await taskApi.startTask(taskId)
      const result = extractData<{ task: Task }>(response)
      if (result?.task) {
        // 用服务器返回的数据更新
        set((state) => ({
          tasks: state.tasks.map((task) =>
            task.id === taskId ? enrichTask(result.task) : task
          )
        }))
      }
    } catch (error) {
      // 请求失败，回滚到之前的状态
      set({ tasks: previousTasks, error: (error as Error).message })
      throw error
    }
  },

  setFilter: (status) => {
    set({ filter: status })
  },
}))
