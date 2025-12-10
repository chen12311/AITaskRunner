export type TemplateType = 'initial_task' | 'continue_task' | 'resume_task' | 'status_check' | 'review' | 'planning'

export interface Template {
  id: string
  name: string
  name_en?: string
  type: TemplateType
  description?: string
  description_en?: string
  content: string
  content_en?: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface CreateTemplateData {
  name: string
  name_en?: string
  type: TemplateType
  description?: string
  description_en?: string
  content: string
  content_en?: string
}

export interface UpdateTemplateData {
  name?: string
  name_en?: string
  type?: TemplateType
  description?: string
  description_en?: string
  content?: string
  content_en?: string
}

export interface RenderTemplateData {
  template_id?: string
  content?: string
  variables: Record<string, string>
}
