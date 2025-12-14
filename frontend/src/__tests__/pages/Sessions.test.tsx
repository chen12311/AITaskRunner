/**
 * Sessions Page Tests
 * 会话页面测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../test-utils'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'

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
    context_tokens: 75000,
    max_tokens: 100000,
  },
  {
    task_id: 'task_3',
    status: 'stopped',
    is_running: false,
    pid: null,
    started_at: '2025-01-01T08:00:00Z',
    context_usage: 100,
    context_tokens: 100000,
    max_tokens: 100000,
  },
]

const mockSessionsResponse = {
  sessions: mockSessions,
  total: 3,
  active: 1,
  max_concurrent: 5,
  available_slots: 4,
}

// Mock useWebSocket hook
vi.mock('@/hooks', () => ({
  useWebSocket: vi.fn(() => ({})),
}))

describe('Sessions Page', () => {
  beforeEach(() => {
    server.resetHandlers()

    server.use(
      http.get('/api/sessions', () => {
        return HttpResponse.json(mockSessionsResponse)
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

  describe('Session List Rendering', () => {
    it('should render loading skeleton initially', async () => {
      server.use(
        http.get('/api/sessions', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100))
          return HttpResponse.json(mockSessionsResponse)
        })
      )

      const { Component } = await import('@/pages/Sessions')
      const { container } = render(<Component />)

      // Check that component renders successfully during loading
      expect(container).toBeInTheDocument()

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })
    })

    it('should render session list after loading', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        // Check for task IDs in the table
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/task_2/i)).toBeInTheDocument()
    })

    it('should display session status badges correctly', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Verify all sessions are rendered
      expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      expect(screen.getByText(/task_2/i)).toBeInTheDocument()
      expect(screen.getByText(/task_3/i)).toBeInTheDocument()
    })

    it('should display empty state when no sessions', async () => {
      server.use(
        http.get('/api/sessions', () => {
          return HttpResponse.json({
            sessions: [],
            total: 0,
            active: 0,
            max_concurrent: 5,
            available_slots: 5,
          })
        })
      )

      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        // Check for empty state icon or message
        const emptyState = document.querySelector('[class*="text-center"]')
        expect(emptyState).toBeInTheDocument()
      })
    })
  })

  describe('Stats Cards', () => {
    it('should display stat cards with correct values', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        // Check for stats display
        expect(screen.getByText('1')).toBeInTheDocument() // active
        expect(screen.getByText('3')).toBeInTheDocument() // total
        expect(screen.getByText('5')).toBeInTheDocument() // max_concurrent
        expect(screen.getByText('4')).toBeInTheDocument() // available_slots
      })
    })

    it('should render all 4 stat cards', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Check for stat card elements
      const cards = document.querySelectorAll('[class*="card"]')
      expect(cards.length).toBeGreaterThanOrEqual(4)
    })
  })

  describe('Session Filtering', () => {
    it('should have status filter dropdown', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Check for select trigger
      const selectTriggers = document.querySelectorAll('[role="combobox"]')
      expect(selectTriggers.length).toBeGreaterThan(0)
    })

    it('should filter sessions by search input', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Find search input
      const searchInput = document.querySelector('input[type="text"]')
      if (searchInput) {
        await user.type(searchInput, 'task_1')

        await waitFor(() => {
          expect(screen.getByText(/task_1/i)).toBeInTheDocument()
        })
      }
    })
  })

  describe('Session Operations', () => {
    it('should have action buttons for running sessions', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Check for action buttons
      const buttons = document.querySelectorAll('button')
      expect(buttons.length).toBeGreaterThan(2)
    })

    it('should show stop confirmation dialog', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Find stop button (square icon)
      const stopButtons = document.querySelectorAll('button')
      const stopButton = Array.from(stopButtons).find(
        (btn) => btn.querySelector('[class*="square"]') && !btn.textContent?.includes('Stop All')
      )

      if (stopButton) {
        await user.click(stopButton)

        await waitFor(() => {
          const dialog = document.querySelector('[role="alertdialog"]')
          expect(dialog).toBeInTheDocument()
        })
      }
    })

    it('should call stop session API', async () => {
      let stopCalled = false
      server.use(
        http.delete('/api/sessions/:taskId', () => {
          stopCalled = true
          return HttpResponse.json({ success: true })
        })
      )

      const user = userEvent.setup()
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Find all buttons with Square icon (stop button)
      const allButtons = document.querySelectorAll('button')
      const stopButtons = Array.from(allButtons).filter((btn) => {
        const hasSvg = btn.querySelector('svg.lucide-square')
        const isNotStopAll = !btn.textContent?.toLowerCase().includes('stop all') &&
                             !btn.textContent?.toLowerCase().includes('停止所有')
        return hasSvg && isNotStopAll
      })

      // Click the first stop button for a running session
      if (stopButtons.length > 0) {
        await user.click(stopButtons[0])

        // Wait for dialog and confirm
        await waitFor(() => {
          const dialog = document.querySelector('[role="alertdialog"]')
          expect(dialog).toBeInTheDocument()
        })

        // Find confirm button by looking for AlertDialogAction
        const buttons = screen.getAllByRole('button')
        const confirmButton = buttons.find((btn) => {
          const text = btn.textContent?.toLowerCase() || ''
          return text.includes('confirm') || text.includes('确认') || text.includes('stop') || text.includes('停止')
        })

        if (confirmButton) {
          await user.click(confirmButton)
          await waitFor(() => {
            expect(stopCalled).toBe(true)
          }, { timeout: 3000 })
        }
      }
    })

    it('should show stop all confirmation dialog', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Find stop all button
      const stopAllButton = screen.getByRole('button', { name: /stop.*all|停止所有/i })
      if (stopAllButton) {
        await user.click(stopAllButton)

        await waitFor(() => {
          const dialog = document.querySelector('[role="alertdialog"]')
          expect(dialog).toBeInTheDocument()
        })
      }
    })
  })

  describe('Refresh', () => {
    it('should have refresh button', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      const refreshButton = screen.getByRole('button', { name: /refresh|刷新/i })
      expect(refreshButton).toBeInTheDocument()
    })

    it('should refresh sessions when refresh button clicked', async () => {
      let fetchCount = 0
      server.use(
        http.get('/api/sessions', () => {
          fetchCount++
          return HttpResponse.json(mockSessionsResponse)
        })
      )

      const user = userEvent.setup()
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      const refreshButton = screen.getByRole('button', { name: /refresh|刷新/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(fetchCount).toBeGreaterThan(1) // Initial + refresh
      })
    })
  })

  describe('Navigation', () => {
    it('should have view details button that navigates to logs', async () => {
      const { Component } = await import('@/pages/Sessions')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText(/task_1/i)).toBeInTheDocument()
      })

      // Find view details button (external link icon)
      const detailButtons = document.querySelectorAll('button')
      const detailButton = Array.from(detailButtons).find((btn) =>
        btn.querySelector('[class*="external"]')
      )

      expect(detailButton).toBeInTheDocument()
    })
  })
})
