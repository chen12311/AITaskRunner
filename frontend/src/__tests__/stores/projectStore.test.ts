/**
 * Project Store Tests
 * 项目状态管理测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { useProjectStore } from '@/stores/projectStore'
import { act } from '@testing-library/react'

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
]

describe('projectStore', () => {
  beforeEach(() => {
    // Reset store state
    useProjectStore.setState({
      projects: [],
      loading: false,
      error: null,
    })

    // Setup default handlers
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
        const project = mockProjects.find((p) => p.id === params.projectId)
        return HttpResponse.json({
          ...project,
          ...body,
          updated_at: new Date().toISOString(),
        })
      }),
      http.delete('/api/projects/:projectId', () => {
        return HttpResponse.json({ success: true })
      })
    )
  })

  afterEach(() => {
    server.resetHandlers()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useProjectStore.getState()
      expect(state.projects).toEqual([])
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
    })
  })

  describe('fetchProjects', () => {
    it('should fetch projects successfully', async () => {
      const { fetchProjects } = useProjectStore.getState()

      await act(async () => {
        await fetchProjects()
      })

      const state = useProjectStore.getState()
      expect(state.projects.length).toBe(2)
      expect(state.projects[0].name).toBe('Project Alpha')
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
    })

    it('should add directory alias field', async () => {
      const { fetchProjects } = useProjectStore.getState()

      await act(async () => {
        await fetchProjects()
      })

      const state = useProjectStore.getState()
      expect(state.projects[0].directory).toBe('/Users/test/projects/alpha')
    })

    it('should set loading state during fetch', async () => {
      server.use(
        http.get('/api/projects', async () => {
          await new Promise((resolve) => setTimeout(resolve, 50))
          return HttpResponse.json(mockProjects)
        })
      )

      const { fetchProjects } = useProjectStore.getState()

      const promise = fetchProjects()

      await new Promise((resolve) => setTimeout(resolve, 10))
      expect(useProjectStore.getState().loading).toBe(true)

      await act(async () => {
        await promise
      })

      expect(useProjectStore.getState().loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      server.use(
        http.get('/api/projects', () => {
          return HttpResponse.json({ error: 'Server error' }, { status: 500 })
        })
      )

      const { fetchProjects } = useProjectStore.getState()

      await act(async () => {
        await fetchProjects()
      })

      const state = useProjectStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('setProjects', () => {
    it('should set projects directly', () => {
      const { setProjects } = useProjectStore.getState()

      act(() => {
        setProjects(mockProjects)
      })

      const state = useProjectStore.getState()
      expect(state.projects.length).toBe(2)
      expect(state.projects[0].directory).toBe('/Users/test/projects/alpha')
    })
  })

  describe('createProject', () => {
    it('should create project and refresh list', async () => {
      const { createProject } = useProjectStore.getState()

      const newProjectData = {
        name: 'Project Gamma',
        description: 'Third project',
        directory_path: '/Users/test/projects/gamma',
      }

      await act(async () => {
        await createProject(newProjectData)
      })

      const state = useProjectStore.getState()
      // Should have refetched (2 original)
      expect(state.projects.length).toBe(2)
    })

    it('should handle create error', async () => {
      server.use(
        http.post('/api/projects', () => {
          return HttpResponse.json({ error: 'Validation error' }, { status: 400 })
        })
      )

      const { createProject } = useProjectStore.getState()

      let threwError = false
      try {
        await act(async () => {
          await createProject({
            name: 'Test',
            description: '',
            directory_path: '/tmp/test',
          })
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useProjectStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('updateProject', () => {
    it('should update project and refresh list', async () => {
      const { updateProject, setProjects } = useProjectStore.getState()

      act(() => {
        setProjects(mockProjects)
      })

      await act(async () => {
        await updateProject('proj_1', { name: 'Project Alpha Updated' })
      })

      const state = useProjectStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle update error', async () => {
      server.use(
        http.put('/api/projects/:projectId', () => {
          return HttpResponse.json({ error: 'Update failed' }, { status: 400 })
        })
      )

      const { updateProject, setProjects } = useProjectStore.getState()

      act(() => {
        setProjects(mockProjects)
      })

      let threwError = false
      try {
        await act(async () => {
          await updateProject('proj_1', { name: 'Updated' })
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useProjectStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('deleteProject', () => {
    it('should delete project and refresh list', async () => {
      const { deleteProject, setProjects } = useProjectStore.getState()

      act(() => {
        setProjects(mockProjects)
      })

      await act(async () => {
        await deleteProject('proj_1')
      })

      const state = useProjectStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle delete error', async () => {
      server.use(
        http.delete('/api/projects/:projectId', () => {
          return HttpResponse.json({ error: 'Cannot delete' }, { status: 500 })
        })
      )

      const { deleteProject, setProjects } = useProjectStore.getState()

      act(() => {
        setProjects(mockProjects)
      })

      let threwError = false
      try {
        await act(async () => {
          await deleteProject('proj_1')
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useProjectStore.getState()
      expect(state.error).toBeTruthy()
    })
  })
})
