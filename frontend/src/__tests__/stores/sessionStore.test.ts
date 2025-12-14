/**
 * Session Store Tests
 * 会话状态管理测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { useSessionStore } from '@/stores/sessionStore'
import { act } from '@testing-library/react'

const mockSessions = [
  {
    task_id: 'task_1',
    status: 'running',
    is_running: true,
    pid: 12345,
    started_at: '2025-01-01T10:00:00Z',
    context_usage: 50,
    context_tokens: 50000,
    max_tokens: 100000,
  },
  {
    task_id: 'task_2',
    status: 'paused',
    is_running: false,
    pid: 12346,
    started_at: '2025-01-01T09:00:00Z',
    context_usage: 75,
  },
]

const mockSessionsResponse = {
  sessions: mockSessions,
  total: 2,
  active: 1,
  max_concurrent: 5,
  available_slots: 4,
}

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('sessionStore', () => {
  beforeEach(() => {
    // Reset store state
    useSessionStore.setState({
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
    })

    // Setup default handlers
    server.use(
      http.get('/api/sessions', () => {
        return HttpResponse.json(mockSessionsResponse)
      }),
      http.get('/api/sessions/active', () => {
        return HttpResponse.json({
          sessions: mockSessions.filter((s) => s.is_running),
          count: 1,
          max_concurrent: 5,
        })
      }),
      http.delete('/api/sessions/:taskId', () => {
        return HttpResponse.json({ success: true })
      }),
      http.post('/api/tasks/:taskId/pause', () => {
        return HttpResponse.json({ success: true })
      }),
      http.post('/api/sessions/stop-all', () => {
        return HttpResponse.json({ success: true })
      })
    )
  })

  afterEach(() => {
    server.resetHandlers()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useSessionStore.getState()
      expect(state.sessions).toEqual([])
      expect(state.stats.total).toBe(0)
      expect(state.stats.active).toBe(0)
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
      expect(state.statusFilter).toBe('all')
    })
  })

  describe('fetchAllSessions', () => {
    it('should fetch all sessions successfully', async () => {
      const { fetchAllSessions } = useSessionStore.getState()

      await act(async () => {
        await fetchAllSessions()
      })

      const state = useSessionStore.getState()
      expect(state.sessions.length).toBe(2)
      expect(state.stats.total).toBe(2)
      expect(state.stats.active).toBe(1)
      expect(state.stats.maxConcurrent).toBe(5)
      expect(state.stats.availableSlots).toBe(4)
    })

    it('should set loading state during fetch', async () => {
      server.use(
        http.get('/api/sessions', async () => {
          await new Promise((resolve) => setTimeout(resolve, 50))
          return HttpResponse.json(mockSessionsResponse)
        })
      )

      const { fetchAllSessions } = useSessionStore.getState()

      const promise = fetchAllSessions()

      await new Promise((resolve) => setTimeout(resolve, 10))
      expect(useSessionStore.getState().loading).toBe(true)

      await act(async () => {
        await promise
      })

      expect(useSessionStore.getState().loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      server.use(
        http.get('/api/sessions', () => {
          return HttpResponse.json({ error: 'Server error' }, { status: 500 })
        })
      )

      const { fetchAllSessions } = useSessionStore.getState()

      await act(async () => {
        await fetchAllSessions()
      })

      const state = useSessionStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('fetchActiveSessions', () => {
    it('should fetch active sessions', async () => {
      const { fetchActiveSessions } = useSessionStore.getState()

      await act(async () => {
        await fetchActiveSessions()
      })

      const state = useSessionStore.getState()
      expect(state.sessions.length).toBe(1)
      expect(state.sessions[0].is_running).toBe(true)
    })
  })

  describe('setSessions', () => {
    it('should set sessions directly', () => {
      const { setSessions } = useSessionStore.getState()

      act(() => {
        setSessions({
          sessions: mockSessions,
          count: 1,
          max_concurrent: 5,
        })
      })

      const state = useSessionStore.getState()
      expect(state.sessions.length).toBe(2)
      expect(state.stats.active).toBe(1)
      expect(state.stats.maxConcurrent).toBe(5)
    })
  })

  describe('stopSession', () => {
    it('should stop session and refresh list', async () => {
      const { stopSession, setSessions } = useSessionStore.getState()

      act(() => {
        setSessions({
          sessions: mockSessions,
          count: 1,
          max_concurrent: 5,
        })
      })

      await act(async () => {
        await stopSession('task_1')
      })

      // Should have refreshed the list
      const state = useSessionStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle stop error', async () => {
      server.use(
        http.delete('/api/sessions/:taskId', () => {
          return HttpResponse.json({ error: 'Cannot stop' }, { status: 500 })
        })
      )

      const { stopSession, setSessions } = useSessionStore.getState()

      act(() => {
        setSessions({
          sessions: mockSessions,
          count: 1,
          max_concurrent: 5,
        })
      })

      await expect(
        act(async () => {
          await stopSession('task_1')
        })
      ).rejects.toThrow()
    })
  })

  describe('pauseSession', () => {
    it('should pause session and refresh list', async () => {
      const { pauseSession, setSessions } = useSessionStore.getState()

      act(() => {
        setSessions({
          sessions: mockSessions,
          count: 1,
          max_concurrent: 5,
        })
      })

      await act(async () => {
        await pauseSession('task_1')
      })

      const state = useSessionStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle pause error', async () => {
      server.use(
        http.post('/api/tasks/:taskId/pause', () => {
          return HttpResponse.json({ error: 'Cannot pause' }, { status: 500 })
        })
      )

      const { pauseSession, setSessions } = useSessionStore.getState()

      act(() => {
        setSessions({
          sessions: mockSessions,
          count: 1,
          max_concurrent: 5,
        })
      })

      await expect(
        act(async () => {
          await pauseSession('task_1')
        })
      ).rejects.toThrow()
    })
  })

  describe('stopAllSessions', () => {
    it('should stop all sessions and refresh list', async () => {
      const { stopAllSessions, setSessions } = useSessionStore.getState()

      act(() => {
        setSessions({
          sessions: mockSessions,
          count: 1,
          max_concurrent: 5,
        })
      })

      await act(async () => {
        await stopAllSessions()
      })

      const state = useSessionStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle stop all error', async () => {
      server.use(
        http.post('/api/sessions/stop-all', () => {
          return HttpResponse.json({ error: 'Cannot stop all' }, { status: 500 })
        })
      )

      const { stopAllSessions, setSessions } = useSessionStore.getState()

      act(() => {
        setSessions({
          sessions: mockSessions,
          count: 1,
          max_concurrent: 5,
        })
      })

      await expect(
        act(async () => {
          await stopAllSessions()
        })
      ).rejects.toThrow()
    })
  })

  describe('setStatusFilter', () => {
    it('should set status filter', () => {
      const { setStatusFilter } = useSessionStore.getState()

      act(() => {
        setStatusFilter('running')
      })

      expect(useSessionStore.getState().statusFilter).toBe('running')

      act(() => {
        setStatusFilter('paused')
      })

      expect(useSessionStore.getState().statusFilter).toBe('paused')

      act(() => {
        setStatusFilter('all')
      })

      expect(useSessionStore.getState().statusFilter).toBe('all')
    })
  })
})
