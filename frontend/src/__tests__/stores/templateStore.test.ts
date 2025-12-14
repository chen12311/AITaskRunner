/**
 * Template Store Tests
 * 模板状态管理测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { useTemplateStore } from '@/stores/templateStore'
import { act } from '@testing-library/react'

const mockTemplates = [
  {
    id: 'tmpl_1',
    name: '初始任务模板',
    name_en: 'Initial Task Template',
    type: 'initial_task',
    description: '用于创建新任务',
    description_en: 'For creating new tasks',
    content: '你是项目经理。请根据以下文档：{{doc_path}}',
    content_en: 'You are a project manager.',
    is_default: true,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 'tmpl_2',
    name: '继续任务模板',
    name_en: 'Continue Task Template',
    type: 'continue_task',
    description: '用于继续执行任务',
    description_en: 'For continuing tasks',
    content: '请继续执行任务',
    content_en: 'Please continue the task',
    is_default: false,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
]

describe('templateStore', () => {
  beforeEach(() => {
    // Reset store state
    useTemplateStore.setState({
      templates: [],
      loading: false,
      error: null,
      filterType: 'all',
    })

    // Setup default handlers
    server.use(
      http.get('/api/templates', () => {
        return HttpResponse.json(mockTemplates)
      }),
      http.post('/api/templates', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(
          {
            id: `tmpl_${Date.now()}`,
            ...body,
            is_default: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          { status: 201 }
        )
      }),
      http.put('/api/templates/:templateId', async ({ params, request }) => {
        const body = (await request.json()) as Record<string, unknown>
        const template = mockTemplates.find((t) => t.id === params.templateId)
        return HttpResponse.json({
          ...template,
          ...body,
          updated_at: new Date().toISOString(),
        })
      }),
      http.delete('/api/templates/:templateId', () => {
        return HttpResponse.json({ success: true })
      }),
      http.post('/api/templates/:templateId/set-default', () => {
        return HttpResponse.json({ success: true })
      })
    )
  })

  afterEach(() => {
    server.resetHandlers()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useTemplateStore.getState()
      expect(state.templates).toEqual([])
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
      expect(state.filterType).toBe('all')
    })
  })

  describe('fetchTemplates', () => {
    it('should fetch templates successfully', async () => {
      const { fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      const state = useTemplateStore.getState()
      expect(state.templates.length).toBe(2)
      expect(state.templates[0].name).toBe('初始任务模板')
      expect(state.loading).toBe(false)
      expect(state.error).toBe(null)
    })

    it('should set loading state during fetch', async () => {
      server.use(
        http.get('/api/templates', async () => {
          await new Promise((resolve) => setTimeout(resolve, 50))
          return HttpResponse.json(mockTemplates)
        })
      )

      const { fetchTemplates } = useTemplateStore.getState()

      const promise = fetchTemplates()

      await new Promise((resolve) => setTimeout(resolve, 10))
      expect(useTemplateStore.getState().loading).toBe(true)

      await act(async () => {
        await promise
      })

      expect(useTemplateStore.getState().loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      server.use(
        http.get('/api/templates', () => {
          return HttpResponse.json({ error: 'Server error' }, { status: 500 })
        })
      )

      const { fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      const state = useTemplateStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('createTemplate', () => {
    it('should create template and refresh list', async () => {
      const { createTemplate } = useTemplateStore.getState()

      const newTemplateData = {
        name: '新模板',
        type: 'review' as const,
        content: '请审查代码',
      }

      await act(async () => {
        await createTemplate(newTemplateData)
      })

      const state = useTemplateStore.getState()
      // Should have refetched
      expect(state.loading).toBe(false)
    })

    it('should handle create error', async () => {
      server.use(
        http.post('/api/templates', () => {
          return HttpResponse.json({ error: 'Validation error' }, { status: 400 })
        })
      )

      const { createTemplate } = useTemplateStore.getState()

      let threwError = false
      try {
        await act(async () => {
          await createTemplate({
            name: 'Test',
            type: 'review',
            content: 'test',
          })
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useTemplateStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('updateTemplate', () => {
    it('should update template and refresh list', async () => {
      const { updateTemplate, fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      await act(async () => {
        await updateTemplate('tmpl_1', { name: '更新后的模板' })
      })

      const state = useTemplateStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle update error', async () => {
      server.use(
        http.put('/api/templates/:templateId', () => {
          return HttpResponse.json({ error: 'Update failed' }, { status: 400 })
        })
      )

      const { updateTemplate, fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      let threwError = false
      try {
        await act(async () => {
          await updateTemplate('tmpl_1', { name: 'Updated' })
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useTemplateStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('deleteTemplate', () => {
    it('should delete template and refresh list', async () => {
      const { deleteTemplate, fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      await act(async () => {
        await deleteTemplate('tmpl_2')
      })

      const state = useTemplateStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle delete error', async () => {
      server.use(
        http.delete('/api/templates/:templateId', () => {
          return HttpResponse.json({ error: 'Cannot delete' }, { status: 500 })
        })
      )

      const { deleteTemplate, fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      let threwError = false
      try {
        await act(async () => {
          await deleteTemplate('tmpl_1')
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useTemplateStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('setDefault', () => {
    it('should set default template and refresh list', async () => {
      const { setDefault, fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      await act(async () => {
        await setDefault('tmpl_2')
      })

      const state = useTemplateStore.getState()
      expect(state.loading).toBe(false)
    })

    it('should handle setDefault error', async () => {
      server.use(
        http.post('/api/templates/:templateId/set-default', () => {
          return HttpResponse.json({ error: 'Cannot set default' }, { status: 500 })
        })
      )

      const { setDefault, fetchTemplates } = useTemplateStore.getState()

      await act(async () => {
        await fetchTemplates()
      })

      let threwError = false
      try {
        await act(async () => {
          await setDefault('tmpl_2')
        })
      } catch {
        threwError = true
      }

      expect(threwError).toBe(true)
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })
      const state = useTemplateStore.getState()
      expect(state.error).toBeTruthy()
    })
  })

  describe('setFilterType', () => {
    it('should set filter type', () => {
      const { setFilterType } = useTemplateStore.getState()

      act(() => {
        setFilterType('initial_task')
      })

      expect(useTemplateStore.getState().filterType).toBe('initial_task')

      act(() => {
        setFilterType('review')
      })

      expect(useTemplateStore.getState().filterType).toBe('review')

      act(() => {
        setFilterType('all')
      })

      expect(useTemplateStore.getState().filterType).toBe('all')
    })
  })
})
