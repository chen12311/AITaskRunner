/**
 * Task Store Tests
 * 任务状态管理测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { useTaskStore } from '@/stores/taskStore'
import { act } from '@testing-library/react'

const mockTasks = [
  {
    id: 'task_1',
    name: 'Test Task 1',
    description: 'First test task',
    status: 'pending',
    project_directory: '/tmp/project1',
    markdown_document_path: '/tmp/project1/TODO.md',
    cli_type: 'claude_code',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 'task_2',
    name: 'Test Task 2',
    description: 'Second test task',
    status: 'in_progress',
    project_directory: '/tmp/project2',
    markdown_document_path: '/tmp/project2/README.md',
    cli_type: 'codex',
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
]

describe('taskStore', () => {
  beforeEach(() => {
    // Reset store state
    useTaskStore.setState({
      tasks: [],
      loading: false,
      error: null,
      filter: 'all',
    })

    // Setup default handlers
    server.use(
      http.get('/api/tasks', () => {
        return HttpResponse.json(mockTasks)
      }),
      http.post('/api/tasks', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(
          {
            id: `task_${Date.now()}`,
            ...body,
            status: 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          { status: 201 }
        )
      }),
      http.put('/api/tasks/:taskId', async ({ params, request }) => {
        const body = (await request.json()) as Record<string, unknown>
        const task = mockTasks.find((t) => t.id === params.taskId)
        return HttpResponse.json({
          ...task,
          ...body,
          updated_at: new Date().toISOString(),
        })
      }),
      http.delete('/api/tasks/:taskId', () => {
        return HttpResponse.json({ success: true })
      }),
      http.post('/api/tasks/:taskId/start', ({ params }) => {
        return HttpResponse.json({
          success: true,
          task: {
            ...mockTasks.find((t) => t.id === params.taskId),
            status: 'in_progress',
          },
        })
      })
    )
  })

  afterEach(() => {
    server.resetHandlers()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useTaskStore.getState()
      expect(state.tasks).toEqual([])
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
      expect(state.filter).toBe('all')
    })
  })

  describe('fetchTasks', () => {
    it('should fetch tasks successfully', async () => {
      const { fetchTasks } = useTaskStore.getState()

      await act(async () => {
        await fetchTasks()
      })

      const state = useTaskStore.getState()
      expect(state.tasks.length).toBe(2)
      expect(state.tasks[0].id).toBe('task_1')
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
    })

    it('should set loading state during fetch', async () => {
      server.use(
        http.get('/api/tasks', async () => {
          await new Promise((resolve) => setTimeout(resolve, 50))
          return HttpResponse.json(mockTasks)
        })
      )

      const { fetchTasks } = useTaskStore.getState()

      const promise = fetchTasks()

      // Check loading is true during fetch
      await new Promise((resolve) => setTimeout(resolve, 10))
      expect(useTaskStore.getState().loading).toBe(true)

      await act(async () => {
        await promise
      })

      expect(useTaskStore.getState().loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      server.use(
        http.get('/api/tasks', () => {
          return HttpResponse.json({ error: 'Server error' }, { status: 500 })
        })
      )

      const { fetchTasks } = useTaskStore.getState()

      await act(async () => {
        await fetchTasks()
      })

      const state = useTaskStore.getState()
      expect(state.error).toBeTruthy()
      expect(state.loading).toBe(false)
    })
  })

  describe('setTasks', () => {
    it('should set tasks directly', () => {
      const { setTasks } = useTaskStore.getState()

      act(() => {
        setTasks(mockTasks)
      })

      const state = useTaskStore.getState()
      expect(state.tasks.length).toBe(2)
      expect(state.tasks[0].project_name).toBeTruthy() // enrichTask adds this
    })

    it('should enrich tasks with display properties', () => {
      const { setTasks } = useTaskStore.getState()

      act(() => {
        setTasks(mockTasks)
      })

      const state = useTaskStore.getState()
      expect(state.tasks[0].project_name).toBe('project1')
      expect(state.tasks[0].doc_path).toBe('TODO.md')
    })
  })

  describe('createTask', () => {
    it('should create task and add to list', async () => {
      const { createTask, setTasks } = useTaskStore.getState()

      // Set initial tasks
      act(() => {
        setTasks(mockTasks)
      })

      const newTaskData = {
        project_directory: '/tmp/project3',
        markdown_document_path: '/tmp/project3/TASK.md',
        cli_type: 'claude_code' as const,
      }

      await act(async () => {
        await createTask(newTaskData)
      })

      const state = useTaskStore.getState()
      expect(state.tasks.length).toBe(3)
      expect(state.tasks[0].project_directory).toBe('/tmp/project3') // New task at beginning
    })

    it('should handle create error', async () => {
      server.use(
        http.post('/api/tasks', () => {
          return HttpResponse.json({ error: 'Validation error' }, { status: 400 })
        })
      )

      const { createTask } = useTaskStore.getState()

      let threwError = false
      try {
        await act(async () => {
          await createTask({
            project_directory: '/tmp/project3',
            markdown_document_path: '/tmp/project3/TASK.md',
            cli_type: 'claude_code',
          })
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      // State check after error is thrown - error should be set in store
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useTaskStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('updateTask', () => {
    it('should update task in list', async () => {
      const { updateTask, setTasks } = useTaskStore.getState()

      act(() => {
        setTasks(mockTasks)
      })

      await act(async () => {
        await updateTask('task_1', { status: 'completed' as const })
      })

      const state = useTaskStore.getState()
      const updatedTask = state.tasks.find((t) => t.id === 'task_1')
      expect(updatedTask?.status).toBe('completed')
    })
  })

  describe('deleteTask', () => {
    it('should delete task from list (optimistic update)', async () => {
      const { deleteTask, setTasks } = useTaskStore.getState()

      act(() => {
        setTasks(mockTasks)
      })

      await act(async () => {
        await deleteTask('task_1')
      })

      const state = useTaskStore.getState()
      expect(state.tasks.length).toBe(1)
      expect(state.tasks.find((t) => t.id === 'task_1')).toBeUndefined()
    })

    it('should rollback on delete error', async () => {
      server.use(
        http.delete('/api/tasks/:taskId', () => {
          return HttpResponse.json({ error: 'Cannot delete' }, { status: 500 })
        })
      )

      const { deleteTask, setTasks } = useTaskStore.getState()

      act(() => {
        setTasks(mockTasks)
      })

      let threwError = false
      try {
        await act(async () => {
          await deleteTask('task_1')
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      // Wait for state update to complete
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      const state = useTaskStore.getState()
      expect(state.tasks.length).toBe(2) // Rolled back
      expect(state.tasks.find((t) => t.id === 'task_1')).toBeTruthy()
    })
  })

  describe('startTask', () => {
    it('should start task (optimistic update)', async () => {
      const { startTask, setTasks } = useTaskStore.getState()

      act(() => {
        setTasks(mockTasks)
      })

      await act(async () => {
        await startTask('task_1')
      })

      const state = useTaskStore.getState()
      const startedTask = state.tasks.find((t) => t.id === 'task_1')
      expect(startedTask?.status).toBe('in_progress')
    })

    it('should rollback on start error', async () => {
      server.use(
        http.post('/api/tasks/:taskId/start', () => {
          return HttpResponse.json({ error: 'Cannot start' }, { status: 500 })
        })
      )

      const { startTask, setTasks } = useTaskStore.getState()

      act(() => {
        setTasks(mockTasks)
      })

      const originalStatus = mockTasks[0].status

      let threwError = false
      try {
        await act(async () => {
          await startTask('task_1')
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      // Wait for state update to complete
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      const state = useTaskStore.getState()
      const task = state.tasks.find((t) => t.id === 'task_1')
      expect(task?.status).toBe(originalStatus) // Rolled back
    })
  })

  describe('setFilter', () => {
    it('should set filter value', () => {
      const { setFilter } = useTaskStore.getState()

      act(() => {
        setFilter('pending')
      })

      expect(useTaskStore.getState().filter).toBe('pending')

      act(() => {
        setFilter('completed')
      })

      expect(useTaskStore.getState().filter).toBe('completed')

      act(() => {
        setFilter('all')
      })

      expect(useTaskStore.getState().filter).toBe('all')
    })
  })
})
