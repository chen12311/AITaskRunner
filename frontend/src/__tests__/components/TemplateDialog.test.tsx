/**
 * TemplateDialog Component Tests
 * 测试 TemplateDialog 组件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../test-utils'
import userEvent from '@testing-library/user-event'
import TemplateDialog from '@/components/TemplateDialog'
import type { Template } from '@/types'

// Mock zustand store
vi.mock('@/stores', () => ({
  useTemplateStore: () => ({
    createTemplate: vi.fn(),
    updateTemplate: vi.fn(),
    fetchTemplates: vi.fn(),
  }),
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const mockTemplate: Template = {
  id: '1',
  name: '测试模板',
  name_en: 'Test Template',
  type: 'initial_task',
  description: '测试模板描述',
  description_en: 'Test template description',
  content: '这是模板内容 {{project_name}}',
  content_en: 'This is template content {{project_name}}',
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
}

describe('TemplateDialog', () => {
  const mockOnOpenChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render create mode dialog', () => {
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    expect(screen.getByText('创建模板')).toBeInTheDocument()
    expect(screen.getByText('模板名称')).toBeInTheDocument()
    expect(screen.getByText('模板类型')).toBeInTheDocument()
    expect(screen.getByText('模板内容')).toBeInTheDocument()
  })

  it('should render edit mode dialog', () => {
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={mockTemplate}
      />
    )

    expect(screen.getByText('编辑模板')).toBeInTheDocument()
  })

  it.skip('should render template type options', async () => {
    // Skip: Radix UI Select doesn't work correctly in jsdom environment
    const user = userEvent.setup()
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    const selectTrigger = screen.getByRole('combobox')
    await user.click(selectTrigger)

    await waitFor(() => {
      expect(screen.getByText('初始任务')).toBeInTheDocument()
      expect(screen.getByText('继续任务')).toBeInTheDocument()
      expect(screen.getByText('恢复任务')).toBeInTheDocument()
      expect(screen.getByText('状态检查')).toBeInTheDocument()
      expect(screen.getByText('审查')).toBeInTheDocument()
      expect(screen.getByText('规划')).toBeInTheDocument()
    })
  })

  it('should render variable buttons', () => {
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    expect(screen.getByText('可用变量:')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '{{project_name}}' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '{{doc_path}}' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '{{task_id}}' })).toBeInTheDocument()
  })

  it('should allow typing in name input', async () => {
    const user = userEvent.setup()
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    const input = screen.getByPlaceholderText('输入模板名称')
    await user.type(input, 'New Template')

    expect(input).toHaveValue('New Template')
  })

  it('should allow typing in content textarea', async () => {
    const user = userEvent.setup()
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    const textarea = screen.getByPlaceholderText('输入模板内容')
    await user.type(textarea, 'Template content here')

    expect(textarea).toHaveValue('Template content here')
  })

  it('should insert variable when variable button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    const variableButton = screen.getByRole('button', { name: '{{project_name}}' })
    await user.click(variableButton)

    const textarea = screen.getByPlaceholderText('输入模板内容')
    expect(textarea).toHaveValue('{{project_name}}')
  })

  it('should call onOpenChange when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    await user.click(screen.getByRole('button', { name: '取消' }))
    expect(mockOnOpenChange).toHaveBeenCalledWith(false)
  })

  it('should have submit button with correct text for create mode', () => {
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    expect(screen.getByRole('button', { name: '创建' })).toBeInTheDocument()
  })

  it('should have submit button with correct text for edit mode', () => {
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={mockTemplate}
      />
    )

    expect(screen.getByRole('button', { name: '保存' })).toBeInTheDocument()
  })

  it('should not render when open is false', () => {
    render(
      <TemplateDialog
        open={false}
        onOpenChange={mockOnOpenChange}
        template={null}
      />
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('should pre-fill form when editing existing template', async () => {
    render(
      <TemplateDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        template={mockTemplate}
      />
    )

    await waitFor(() => {
      expect(screen.getByDisplayValue('测试模板')).toBeInTheDocument()
      expect(screen.getByDisplayValue('测试模板描述')).toBeInTheDocument()
    })
  })
})
