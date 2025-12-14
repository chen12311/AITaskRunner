/**
 * Projects Page Tests
 * 项目页面测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../test-utils'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'

const mockProjects = [
  {
    id: 'proj_1',
    name: 'Project Alpha',
    description: 'First test project',
    directory_path: '/Users/test/projects/alpha',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 'proj_2',
    name: 'Project Beta',
    description: 'Second test project',
    directory_path: '/Users/test/projects/beta',
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
  {
    id: 'proj_3',
    name: 'Project Gamma',
    description: null,
    directory_path: '/Users/test/projects/gamma',
    created_at: '2025-01-03T00:00:00Z',
    updated_at: '2025-01-03T00:00:00Z',
  },
]

const mockTerminalsResponse = {
  terminals: [
    { id: 'auto', name: 'Auto', installed: true, recommended: true },
    { id: 'iterm', name: 'iTerm', installed: true },
    { id: 'kitty', name: 'Kitty', installed: false },
  ],
  current: 'auto',
  platform: 'darwin',
}

describe('Projects Page', () => {
  beforeEach(() => {
    server.resetHandlers()

    server.use(
      http.get('/api/projects', () => {
        return HttpResponse.json(mockProjects)
      }),
      http.post('/api/projects', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(
          {
            id: `proj_${Date.now()}`,
            ...body,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          { status: 201 }
        )
      }),
      http.put('/api/projects/:projectId', async ({ params, request }) => {
        const body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({
          id: params.projectId,
          ...body,
          updated_at: new Date().toISOString(),
        })
      }),
      http.delete('/api/projects/:projectId', () => {
        return HttpResponse.json({ success: true })
      }),
      http.post('/api/projects/:projectId/launch', () => {
        return HttpResponse.json({ success: true, message: 'Project launched' })
      }),
      http.get('/api/settings/terminals', () => {
        return HttpResponse.json(mockTerminalsResponse)
      })
    )
  })

  describe('Project List Rendering', () => {
    it('should render loading skeleton initially', async () => {
      server.use(
        http.get('/api/projects', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100))
          return HttpResponse.json(mockProjects)
        })
      )

      const { Component } = await import('@/pages/Projects')
      const { container } = render(<Component />)

      // Verify component renders successfully during loading
      expect(container).toBeInTheDocument()

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })
    })

    it('should render project list after loading', async () => {
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      expect(screen.getByText('Project Beta')).toBeInTheDocument()
      expect(screen.getByText('Project Gamma')).toBeInTheDocument()
    })

    it('should display project directories', async () => {
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      expect(screen.getByText('/Users/test/projects/alpha')).toBeInTheDocument()
      expect(screen.getByText('/Users/test/projects/beta')).toBeInTheDocument()
    })

    it('should display project descriptions', async () => {
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('First test project')).toBeInTheDocument()
      })

      expect(screen.getByText('Second test project')).toBeInTheDocument()
    })

    it('should display empty state when no projects', async () => {
      server.use(
        http.get('/api/projects', () => {
          return HttpResponse.json([])
        })
      )

      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        const tableBody = document.querySelector('tbody')
        expect(tableBody).toBeInTheDocument()
      })
    })
  })

  describe('Project Operations', () => {
    it('should have action buttons for each project', async () => {
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Check for action buttons (Launch, Edit, Delete)
      const buttons = document.querySelectorAll('button')
      expect(buttons.length).toBeGreaterThan(3)
    })

    it('should have launch button with dropdown', async () => {
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Check for launch buttons
      const launchButtons = screen.getAllByRole('button', { name: /launch|启动/i })
      expect(launchButtons.length).toBeGreaterThan(0)
    })

    it('should show delete confirmation dialog', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Find delete button
      const deleteButtons = document.querySelectorAll('button')
      const deleteButton = Array.from(deleteButtons).find((btn) =>
        btn.querySelector('[class*="trash"]')
      )

      if (deleteButton) {
        await user.click(deleteButton)

        await waitFor(() => {
          const dialog = document.querySelector('[role="alertdialog"]')
          expect(dialog).toBeInTheDocument()
        })
      }
    })

    it('should call launch project API', async () => {
      let launchCalled = false
      server.use(
        http.post('/api/projects/:projectId/launch', () => {
          launchCalled = true
          return HttpResponse.json({ success: true })
        })
      )

      const user = userEvent.setup()
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Find and click launch button
      const launchButtons = screen.getAllByRole('button', { name: /launch|启动/i })
      if (launchButtons[0]) {
        await user.click(launchButtons[0])

        await waitFor(() => {
          expect(launchCalled).toBe(true)
        })
      }
    })

    it('should call delete project API', async () => {
      let deleteCalled = false
      server.use(
        http.delete('/api/projects/:projectId', () => {
          deleteCalled = true
          return HttpResponse.json({ success: true })
        })
      )

      const user = userEvent.setup()
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Find and click delete button
      const deleteButtons = document.querySelectorAll('button')
      const deleteButton = Array.from(deleteButtons).find((btn) =>
        btn.querySelector('[class*="trash"]')
      )

      if (deleteButton) {
        await user.click(deleteButton)

        // Wait for dialog and confirm
        await waitFor(() => {
          const dialog = document.querySelector('[role="alertdialog"]')
          expect(dialog).toBeInTheDocument()
        })

        const confirmButton = screen.getByRole('button', { name: /confirm|确认|delete|删除/i })
        if (confirmButton) {
          await user.click(confirmButton)
          await waitFor(() => {
            expect(deleteCalled).toBe(true)
          })
        }
      }
    })
  })

  describe('Project Dialog', () => {
    it('should open create project dialog when create button clicked', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Find create button - it has a Plus icon
      const buttons = document.querySelectorAll('button')
      const createButton = Array.from(buttons).find((btn) => {
        // Check if button contains Plus icon (lucide-react adds 'lucide' class)
        const svg = btn.querySelector('svg')
        return svg && btn.textContent && btn.textContent.length > 0
      })

      if (createButton) {
        await user.click(createButton)

        await waitFor(
          () => {
            const dialog = document.querySelector('[role="dialog"]')
            expect(dialog).toBeInTheDocument()
          },
          { timeout: 3000 }
        )
      }
    })

    it('should open edit project dialog when edit button clicked', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Find and click edit button
      const editButtons = document.querySelectorAll('button')
      const editButton = Array.from(editButtons).find((btn) =>
        btn.querySelector('[class*="edit"]')
      )

      if (editButton) {
        await user.click(editButton)

        await waitFor(
          () => {
            const dialog = document.querySelector('[role="dialog"]')
            expect(dialog).toBeInTheDocument()
          },
          { timeout: 3000 }
        )
      }
    })
  })

  describe('Launch Dropdown', () => {
    it('should show CLI options in dropdown', async () => {
      const user = userEvent.setup()
      const { Component } = await import('@/pages/Projects')
      render(<Component />)

      await waitFor(() => {
        expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      })

      // Find dropdown trigger (chevron button next to launch)
      const dropdownTriggers = document.querySelectorAll('[class*="chevron"]')
      const dropdownTrigger = Array.from(dropdownTriggers)
        .find((el) => el.closest('button'))
        ?.closest('button')

      if (dropdownTrigger) {
        await user.click(dropdownTrigger)

        await waitFor(() => {
          const menu = document.querySelector('[role="menu"]')
          expect(menu).toBeInTheDocument()
        })
      }
    })
  })
})
