import { create } from 'zustand'
import { templateApi } from '@/api'
import { extractData, isSuccess } from '@/api/client'
import type { Template, TemplateType } from '@/types/template'

interface TemplateState {
  templates: Template[]
  loading: boolean
  error: string | null
  filterType: TemplateType | 'all'

  fetchTemplates: () => Promise<void>
  createTemplate: (data: Parameters<typeof templateApi.createTemplate>[0]) => Promise<void>
  updateTemplate: (templateId: string, data: Parameters<typeof templateApi.updateTemplate>[1]) => Promise<void>
  deleteTemplate: (templateId: string) => Promise<void>
  setDefault: (templateId: string) => Promise<void>
  setFilterType: (type: TemplateType | 'all') => void
}

export const useTemplateStore = create<TemplateState>((set, get) => ({
  templates: [],
  loading: false,
  error: null,
  filterType: 'all',

  fetchTemplates: async () => {
    set({ loading: true, error: null })
    try {
      const response = await templateApi.getAllTemplates()
      // 后端直接返回数组
      const templates = extractData<Template[]>(response)
      set({ templates })
    } catch (error) {
      set({ error: (error as Error).message })
    } finally {
      set({ loading: false })
    }
  },

  createTemplate: async (data) => {
    set({ loading: true, error: null })
    try {
      const response = await templateApi.createTemplate(data)
      if (isSuccess(response)) {
        await get().fetchTemplates()
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },

  updateTemplate: async (templateId, data) => {
    set({ loading: true, error: null })
    try {
      const response = await templateApi.updateTemplate(templateId, data)
      if (isSuccess(response)) {
        await get().fetchTemplates()
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },

  deleteTemplate: async (templateId) => {
    set({ loading: true, error: null })
    try {
      const response = await templateApi.deleteTemplate(templateId)
      if (isSuccess(response)) {
        await get().fetchTemplates()
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    } finally {
      set({ loading: false })
    }
  },

  setDefault: async (templateId) => {
    try {
      const response = await templateApi.setDefault(templateId)
      if (isSuccess(response)) {
        await get().fetchTemplates()
      }
    } catch (error) {
      set({ error: (error as Error).message })
      throw error
    }
  },

  setFilterType: (type) => {
    set({ filterType: type })
  },
}))
