export interface Project {
  id: string
  name: string
  directory_path: string
  description?: string
  created_at: string
  updated_at: string
  // 兼容字段
  directory?: string
}

export interface CreateProjectData {
  name: string
  directory_path: string
  description?: string
}

export interface UpdateProjectData {
  name?: string
  directory_path?: string
  description?: string
}
