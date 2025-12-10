import client from './client'
import type { Session } from '@/types'

interface SessionsResponse {
  sessions: Session[]
  count: number
  max_concurrent: number
}

export const sessionsApi = {
  getAllSessions(): Promise<Session[]> {
    return client.get('/sessions')
  },

  getActiveSessions(): Promise<SessionsResponse> {
    return client.get('/sessions/active')
  },

  getSession(taskId: string): Promise<Session> {
    return client.get(`/sessions/${taskId}`)
  },

  removeSession(taskId: string): Promise<void> {
    return client.delete(`/sessions/${taskId}`)
  },

  stopAll(): Promise<void> {
    return client.post('/sessions/stop-all')
  },
}
