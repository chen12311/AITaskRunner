/**
 * TaskDialog Component Tests
 * 测试 TaskDialog 组件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../test-utils'
import userEvent from '@testing-library/user-event'
import TaskDialog from '@/components/TaskDialog'
import type { Task, Project } from '@/types'

// Mock zustand store
vi.mock('@/stores', () => ({
  useTaskStore: () => ({
    createTask: vi.fn(),
    updateTask: vi.fn(),
    fetchTasks: vi.fn(),
  }),
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Project 1',
    directory: '/path/to/project1',
    directory_path: '/path/to/project1',
    description: 'Test project 1',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
  {
    id: '2',
    name: 'Project 2',
    directory: '/path/to/project2',
    directory_path: '/path/to/project2',
    description: 'Test project 2',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
]

const mockTask: Task = {
  id: 'task-1',
  project_directory: '/path/to/project1',
  markdown_document_path: '/path/to/project1/docs/test.md',
  status: 'pending',
  cli_type: 'claude_code',
  enable_review: true,
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
}

describe('TaskDialog', () => {
  const mockOnOpenChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render create mode dialog', () => {
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={null}
        projects={mockProjects}
      />
    )

    expect(screen.getByText('创建任务')).toBeInTheDocument()
    expect(screen.getByText('项目')).toBeInTheDocument()
    expect(screen.getByText('文档路径')).toBeInTheDocument()
  })

  it('should render edit mode dialog with task data', () => {
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={mockTask}
        projects={mockProjects}
      />
    )

    expect(screen.getByText('编辑任务')).toBeInTheDocument()
  })

  it('should render enable review radio options', () => {
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={null}
        projects={mockProjects}
      />
    )

    expect(screen.getByText('启用审查')).toBeInTheDocument()
    expect(screen.getByText('继承项目设置')).toBeInTheDocument()
    expect(screen.getByText('启用')).toBeInTheDocument()
    expect(screen.getByText('禁用')).toBeInTheDocument()
  })

  it('should call onOpenChange when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={null}
        projects={mockProjects}
      />
    )

    await user.click(screen.getByRole('button', { name: '取消' }))
    expect(mockOnOpenChange).toHaveBeenCalledWith(false)
  })

  it('should have submit button with correct text for create mode', () => {
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={null}
        projects={mockProjects}
      />
    )

    expect(screen.getByRole('button', { name: '创建' })).toBeInTheDocument()
  })

  it('should have submit button with correct text for edit mode', () => {
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={mockTask}
        projects={mockProjects}
      />
    )

    expect(screen.getByRole('button', { name: '保存' })).toBeInTheDocument()
  })

  it('should allow typing in document path input', async () => {
    const user = userEvent.setup()
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={null}
        projects={mockProjects}
      />
    )

    const input = screen.getByPlaceholderText('输入文档相对路径')
    await user.type(input, 'docs/README.md')

    expect(input).toHaveValue('docs/README.md')
  })

  it('should not render when open is false', () => {
    render(
      <TaskDialog
        open={false}
        onOpenChange={mockOnOpenChange}
        task={null}
        projects={mockProjects}
      />
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it.skip('should render project select options', async () => {
    // Skip: Radix UI Select doesn't work correctly in jsdom environment
    const user = userEvent.setup()
    render(
      <TaskDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        task={null}
        projects={mockProjects}
      />
    )

    // Find and click the project select trigger
    const selectTriggers = screen.getAllByRole('combobox')
    await user.click(selectTriggers[0])

    await waitFor(() => {
      expect(screen.getByText('Project 1')).toBeInTheDocument()
      expect(screen.getByText('Project 2')).toBeInTheDocument()
    })
  })
})
