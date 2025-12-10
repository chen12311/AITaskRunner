import client from './client'
import type { Template, CreateTemplateData, UpdateTemplateData, RenderTemplateData } from '@/types'

export const templateApi = {
  getAllTemplates(): Promise<Template[]> {
    return client.get('/templates')
  },

  getTemplatesByType(type: string): Promise<Template[]> {
    return client.get(`/templates/type/${type}`)
  },

  getTemplate(templateId: string): Promise<Template> {
    return client.get(`/templates/${templateId}`)
  },

  createTemplate(data: CreateTemplateData): Promise<Template> {
    return client.post('/templates', data)
  },

  updateTemplate(templateId: string, data: UpdateTemplateData): Promise<Template> {
    return client.put(`/templates/${templateId}`, data)
  },

  deleteTemplate(templateId: string): Promise<void> {
    return client.delete(`/templates/${templateId}`)
  },

  setDefault(templateId: string): Promise<void> {
    return client.post(`/templates/${templateId}/set-default`)
  },

  render(data: RenderTemplateData): Promise<{ rendered: string }> {
    return client.post('/templates/render', data)
  },
}
