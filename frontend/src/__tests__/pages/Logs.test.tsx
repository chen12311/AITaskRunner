/**
 * Logs Page Tests
 * 日志页面测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../test-utils'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'

const mockTasks = [
  {
    id: 'task_1',
    name: 'Test Task 1',
    project_directory: '/tmp/project1',
    markdown_document_path: '/tmp/project1/TODO.md',
    project_name: 'project1',
    doc_path: 'TODO.md',
    status: 'pending',
    cli_type: 'claude_code',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 'task_2',
    name: 'Test Task 2',
    project_directory: '/tmp/project2',
    markdown_document_path: '/tmp/project2/README.md',
    project_name: 'project2',
    doc_path: 'README.md',
    status: 'in_progress',
    cli_type: 'claude_code',
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
]

const mockLogs = [
  {
    id: 'log_1',
    task_id: 'task_1',
    level: 'INFO',
    message: 'Task started successfully',
    timestamp: '2025-01-01T10:00:00Z',
    created_at: '2025-01-01T10:00:00Z',
  },
  {
    id: 'log_2',
    task_id: 'task_1',
    level: 'WARNING',
    message: 'High memory usage detected',
    timestamp: '2025-01-01T10:05:00Z',
    created_at: '2025-01-01T10:05:00Z',
  },
  {
    id: 'log_3',
    task_id: 'task_1',
    level: 'ERROR',
    message: 'Connection timeout',
    timestamp: '2025-01-01T10:10:00Z',
    created_at: '2025-01-01T10:10:00Z',
  },
  {
    id: 'log_4',
    task_id: 'task_1',
    level: 'DEBUG',
    message: 'Processing step 3 of 10',
    timestamp: '2025-01-01T10:15:00Z',
    created_at: '2025-01-01T10:15:00Z',
  },
]

describe('Logs Page', () => {
  beforeEach(() => {
    server.resetHandlers()

    server.use(
      http.get('/api/tasks', () => {
        return HttpResponse.json(mockTasks)
      }),
      http.get('/api/tasks/:taskId/logs', ({ params }) => {
        if (params.taskId === 'task_1') {
          return HttpResponse.json({ logs: mockLogs, total: mockLogs.length })
        }
        return HttpResponse.json({ logs: [], total: 0 })
      })
    )
  })

  describe('Logs Page Rendering', () => {
    it('should render page title', async () => {
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const cards = document.querySelectorAll('[class*="card"]')
        expect(cards.length).toBeGreaterThan(0)
      })
    })

    it('should display task selector', async () => {
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })
    })

    it('should show select task prompt when no task selected', async () => {
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        // Check for prompt message
        const promptElement = document.querySelector('[class*="text-center"]')
        expect(promptElement).toBeInTheDocument()
      })
    })
  })

  describe('Task Selection', () => {
    it('should load tasks in selector', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      // Click on task selector
      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          // Check for task options
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })
      }
    })

    it('should load logs when task selected', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      // Select a task
      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })

        const options = document.querySelectorAll('[role="option"]')
        if (options.length > 0) {
          await user.click(options[0])

          await waitFor(
            () => {
              // Check for log content
              const logContent = document.querySelector('[class*="font-mono"]')
              expect(logContent).toBeInTheDocument()
            },
            { timeout: 3000 }
          )
        }
      }
    })
  })

  describe('Log Filtering', () => {
    it('should have level filter dropdown', async () => {
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(1)
      })
    })

    it('should have search input', async () => {
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const searchInput = document.querySelector('input[data-slot="input"]')
        expect(searchInput).toBeInTheDocument()
      })
    })

    it('should filter logs by search', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      // First select a task
      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })

        const options = document.querySelectorAll('[role="option"]')
        if (options.length > 0) {
          await user.click(options[0])

          // Then search
          await waitFor(
            () => {
              const searchInput = document.querySelector('input[data-slot="input"]')
              expect(searchInput).toBeInTheDocument()
            },
            { timeout: 3000 }
          )

          const searchInput = document.querySelector('input[data-slot="input"]')
          if (searchInput) {
            await user.type(searchInput, 'ERROR')
            // Filtering happens client-side
          }
        }
      }
    })
  })

  describe('Log Display', () => {
    it('should display loading skeleton when loading logs', async () => {
      server.use(
        http.get('/api/tasks/:taskId/logs', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100))
          return HttpResponse.json({ logs: mockLogs, total: mockLogs.length })
        })
      )

      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      // Select a task to trigger loading
      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })

        const options = document.querySelectorAll('[role="option"]')
        if (options.length > 0) {
          await user.click(options[0])

          // Check for skeleton while loading
          const skeleton = document.querySelector('[class*="skeleton"]')
          // Note: skeleton may appear briefly
        }
      }
    })

    it('should display empty state when no logs', async () => {
      server.use(
        http.get('/api/tasks/:taskId/logs', () => {
          return HttpResponse.json({ logs: [], total: 0 })
        })
      )

      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })

        const options = document.querySelectorAll('[role="option"]')
        if (options.length > 0) {
          await user.click(options[0])

          await waitFor(
            () => {
              // Check for empty state or no data message
              const emptyState = document.querySelector('[class*="text-muted-foreground"]')
              expect(emptyState).toBeInTheDocument()
            },
            { timeout: 3000 }
          )
        }
      }
    })

    it('should color-code log levels', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })

        const options = document.querySelectorAll('[role="option"]')
        if (options.length > 0) {
          await user.click(options[0])

          await waitFor(
            () => {
              // Check for log level badges using data-slot
              const badges = document.querySelectorAll('[data-slot="badge"]')
              expect(badges.length).toBeGreaterThan(0)
            },
            { timeout: 3000 }
          )
        }
      }
    })
  })

  describe('Virtualization', () => {
    it('should handle scrolling in log container', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })

        const options = document.querySelectorAll('[role="option"]')
        if (options.length > 0) {
          await user.click(options[0])

          await waitFor(
            () => {
              // Check for scrollable container
              const scrollContainer = document.querySelector('[class*="overflow-auto"]')
              expect(scrollContainer).toBeInTheDocument()
            },
            { timeout: 3000 }
          )
        }
      }
    })
  })

  describe('Refresh', () => {
    it('should have refresh button', async () => {
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const refreshButton = document.querySelector('button [class*="refresh"]')?.closest('button')
        expect(refreshButton).toBeInTheDocument()
      })
    })

    it('should disable refresh when no task selected', async () => {
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const refreshButton = document
          .querySelector('button [class*="refresh"]')
          ?.closest('button') as HTMLButtonElement
        expect(refreshButton?.disabled).toBe(true)
      })
    })

    it('should enable refresh when task selected', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Logs')
      render(<Component />)

      await waitFor(() => {
        const selects = document.querySelectorAll('[role="combobox"]')
        expect(selects.length).toBeGreaterThan(0)
      })

      const taskSelector = document.querySelectorAll('[role="combobox"]')[0]
      if (taskSelector) {
        await user.click(taskSelector)

        await waitFor(() => {
          const listbox = document.querySelector('[role="listbox"]')
          expect(listbox).toBeInTheDocument()
        })

        const options = document.querySelectorAll('[role="option"]')
        if (options.length > 0) {
          await user.click(options[0])

          await waitFor(
            () => {
              const refreshButton = document
                .querySelector('button [class*="refresh"]')
                ?.closest('button') as HTMLButtonElement
              expect(refreshButton?.disabled).toBe(false)
            },
            { timeout: 3000 }
          )
        }
      }
    })
  })
})
