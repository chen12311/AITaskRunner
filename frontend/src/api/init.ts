/**
 * 初始化API (优化1.1)
 * 合并 tasks + sessions + projects + settings 为单个请求
 */
import client from './client'
import type { Task, Project, Session, SettingsMap } from '@/types'

export interface InitResponse {
  tasks: Task[]
  sessions: {
    sessions: Session[]
    count: number
    max_concurrent: number
  }
  projects: Project[]
  settings: {
    settings: SettingsMap
  }
}

export const initApi = {
  /**
   * 获取前端初始化所需的所有数据
   * 替代原来的 4 个独立请求
   */
  getInitData(): Promise<InitResponse> {
    return client.get('/init')
  },
}
