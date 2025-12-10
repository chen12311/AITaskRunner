import { create } from 'zustand'
import { projectApi } from '@/api'
import { extractData, isSuccess } from '@/api/client'
import type { Project } from '@/types/project'

interface ProjectState {
  projects: Project[]
  loading: boolean
  error: string | null

  fetchProjects: () => Promise<void>
  setProjects: (projects: Project[]) => void  // 优化1.1: 直接设置项目列表
  createProject: (data: Parameters<typeof projectApi.createProject>[0]) => Promise<void>
  updateProject: (projectId: string, data: Parameters<typeof projectApi.updateProject>[1]) => Promise<void>
  deleteProject: (projectId: string) => Promise<void>
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null })
    try {
      const response = await projectApi.getAllProjects()
      // 后端直接返回数组，添加兼容字段
      const projects = extractData<Project[]>(response).map(p => ({
        ...p,
        directory: p.directory_path, // 兼容旧字段名
      }))
      set({ projects })
    } catch (error) {
      set({ error: (error as Error).message })
    } finally {
      set({ loading: false })
    }
  },

  // 优化1.1: 直接设置项目列表（用于批量初始化）
  setProjects: (projects: Project[]) => {
    set({
      projects: projects.map(p => ({
        ...p,
        directory: p.directory_path, // 兼容旧字段名
      }))
    })
  },

  createProject: async (data) => {
    set({ loading: true, error: null })
    try {
      const response = await projectApi.createProject(data)
      if (isSuccess(response)) {
        await get().fetchProjects()
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },

  updateProject: async (projectId, data) => {
    set({ loading: true, error: null })
    try {
      const response = await projectApi.updateProject(projectId, data)
      if (isSuccess(response)) {
        await get().fetchProjects()
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },

  deleteProject: async (projectId) => {
    set({ loading: true, error: null })
    try {
      const response = await projectApi.deleteProject(projectId)
      if (isSuccess(response)) {
        await get().fetchProjects()
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },
}))
