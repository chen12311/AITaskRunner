import client from './client'
import type { Project, CreateProjectData, UpdateProjectData } from '@/types'

export interface LaunchProjectData {
  command?: string
  mode?: 'cli' | 'terminal'
  terminal?: 'iterm' | 'kitty' | 'windows_terminal'
  dangerousMode?: boolean
}

export interface LaunchProjectResponse {
  success: boolean
  message: string
  session_id?: string
  command?: string
  project_directory?: string
}

export const projectApi = {
  getAllProjects(): Promise<Project[]> {
    return client.get('/projects')
  },

  getProject(projectId: string): Promise<Project> {
    return client.get(`/projects/${projectId}`)
  },

  createProject(data: CreateProjectData): Promise<Project> {
    return client.post('/projects', data)
  },

  updateProject(projectId: string, data: UpdateProjectData): Promise<Project> {
    return client.put(`/projects/${projectId}`, data)
  },

  deleteProject(projectId: string): Promise<void> {
    return client.delete(`/projects/${projectId}`)
  },

  launchProject(projectId: string, data?: LaunchProjectData): Promise<LaunchProjectResponse> {
    return client.post(`/projects/${projectId}/launch`, data || {})
  },
}
