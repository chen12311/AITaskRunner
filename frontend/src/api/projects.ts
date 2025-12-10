import client from './client'
import type { Project, CreateProjectData, UpdateProjectData } from '@/types'

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
}
