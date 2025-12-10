import { create } from 'zustand'
import { sessionsApi, taskApi } from '@/api'
import { toast } from 'sonner'
import i18n from '@/i18n'
import type { Session, SessionStats, SessionStatusFilter } from '@/types/task'

interface SessionStore {
  // 数据
  sessions: Session[]
  stats: SessionStats
  loading: boolean
  error: string | null
  statusFilter: SessionStatusFilter

  // 操作
  fetchAllSessions: () => Promise<void>
  fetchActiveSessions: () => Promise<void>
  setSessions: (data: { sessions: Session[]; count: number; max_concurrent: number }) => void  // 优化1.1
  stopSession: (taskId: string) => Promise<void>
  pauseSession: (taskId: string) => Promise<void>
  stopAllSessions: () => Promise<void>
  setStatusFilter: (filter: SessionStatusFilter) => void
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  // 初始状态
  sessions: [],
  stats: {
    total: 0,
    active: 0,
    maxConcurrent: 3,
    availableSlots: 3,
  },
  loading: false,
  error: null,
  statusFilter: 'all',

  // 获取所有会话（含统计信息）
  fetchAllSessions: async () => {
    set({ loading: true, error: null })
    try {
      const response = await sessionsApi.getAllSessions()

      // 后端返回 {sessions, total, active, max_concurrent, available_slots}
      const data: {
        sessions?: Session[]
        total?: number
        active?: number
        max_concurrent?: number
        available_slots?: number
      } = response as unknown as Record<string, unknown>

      set({
        sessions: data.sessions || [],
        stats: {
          total: data.total || 0,
          active: data.active || 0,
          maxConcurrent: data.max_concurrent || 3,
          availableSlots: data.available_slots || 0,
        },
      })
    } catch (error) {
      const errorMessage = (error as Error).message
      set({ error: errorMessage })
      console.error('Failed to fetch sessions:', error)
    } finally {
      set({ loading: false })
    }
  },

  // 获取活跃会话
  fetchActiveSessions: async () => {
    set({ loading: true, error: null })
    try {
      const response = await sessionsApi.getActiveSessions()

      // 后端返回 {sessions, count, max_concurrent}
      const data: {
        sessions?: Session[]
        count?: number
        max_concurrent?: number
      } = response as unknown as Record<string, unknown>

      set({
        sessions: data.sessions || [],
        stats: {
          ...get().stats,
          active: data.count || 0,
          maxConcurrent: data.max_concurrent || 3,
        },
      })
    } catch (error) {
      const errorMessage = (error as Error).message
      set({ error: errorMessage })
      console.error('Failed to fetch active sessions:', error)
    } finally {
      set({ loading: false })
    }
  },

  // 优化1.1: 直接设置会话数据（用于批量初始化）
  setSessions: (data: { sessions: Session[]; count: number; max_concurrent: number }) => {
    set({
      sessions: data.sessions || [],
      stats: {
        ...get().stats,
        active: data.count || 0,
        maxConcurrent: data.max_concurrent || 3,
      },
    })
  },

  // 停止单个会话
  stopSession: async (taskId: string) => {
    try {
      await sessionsApi.removeSession(taskId)
      toast.success(i18n.t('sessions.toast.stopSuccess'))

      // 刷新会话列表
      await get().fetchAllSessions()
    } catch (error) {
      const errorMessage = (error as Error).message
      toast.error(i18n.t('sessions.toast.stopFailed', { message: errorMessage }))
      throw error
    }
  },

  // 暂停会话
  pauseSession: async (taskId: string) => {
    try {
      await taskApi.pauseTask(taskId)
      toast.success(i18n.t('sessions.toast.pauseSuccess'))

      // 刷新会话列表
      await get().fetchAllSessions()
    } catch (error) {
      const errorMessage = (error as Error).message
      toast.error(i18n.t('sessions.toast.pauseFailed', { message: errorMessage }))
      throw error
    }
  },

  // 停止所有会话
  stopAllSessions: async () => {
    try {
      await sessionsApi.stopAll()
      toast.success(i18n.t('sessions.toast.stopAllSuccess'))

      // 刷新会话列表
      await get().fetchAllSessions()
    } catch (error) {
      const errorMessage = (error as Error).message
      toast.error(i18n.t('sessions.toast.stopAllFailed', { message: errorMessage }))
      throw error
    }
  },

  // 设置状态筛选
  setStatusFilter: (filter: SessionStatusFilter) => {
    set({ statusFilter: filter })
  },
}))
