/**
 * ProjectDialog Component Tests
 * 测试 ProjectDialog 组件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../test-utils'
import userEvent from '@testing-library/user-event'
import ProjectDialog from '@/components/ProjectDialog'
import type { Project } from '@/types'

// Mock zustand store
vi.mock('@/stores', () => ({
  useProjectStore: () => ({
    createProject: vi.fn(),
    updateProject: vi.fn(),
    fetchProjects: vi.fn(),
  }),
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const mockProject: Project = {
  id: '1',
  name: 'Test Project',
  directory: '/path/to/project',
  directory_path: '/path/to/project',
  description: 'Test project description',
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
}

describe('ProjectDialog', () => {
  const mockOnOpenChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render create mode dialog', () => {
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    expect(screen.getByText('创建项目')).toBeInTheDocument()
    expect(screen.getByText('项目名称')).toBeInTheDocument()
    expect(screen.getByText('项目目录')).toBeInTheDocument()
    expect(screen.getByText('描述')).toBeInTheDocument()
  })

  it('should render edit mode dialog with project data', async () => {
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={mockProject}
      />
    )

    expect(screen.getByText('编辑项目')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Project')).toBeInTheDocument()
      expect(screen.getByDisplayValue('/path/to/project')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Test project description')).toBeInTheDocument()
    })
  })

  it('should allow typing in name input', async () => {
    const user = userEvent.setup()
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    const input = screen.getByPlaceholderText('输入项目名称')
    await user.type(input, 'New Project')

    expect(input).toHaveValue('New Project')
  })

  it('should allow typing in directory input', async () => {
    const user = userEvent.setup()
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    const input = screen.getByPlaceholderText('输入项目目录路径')
    await user.type(input, '/home/user/projects/new')

    expect(input).toHaveValue('/home/user/projects/new')
  })

  it('should allow typing in description textarea', async () => {
    const user = userEvent.setup()
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    const textarea = screen.getByPlaceholderText('输入项目描述（可选）')
    await user.type(textarea, 'This is a test description')

    expect(textarea).toHaveValue('This is a test description')
  })

  it('should call onOpenChange when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    await user.click(screen.getByRole('button', { name: '取消' }))
    expect(mockOnOpenChange).toHaveBeenCalledWith(false)
  })

  it('should have submit button with correct text for create mode', () => {
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    expect(screen.getByRole('button', { name: '创建' })).toBeInTheDocument()
  })

  it('should have submit button with correct text for edit mode', () => {
    render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={mockProject}
      />
    )

    expect(screen.getByRole('button', { name: '保存' })).toBeInTheDocument()
  })

  it('should not render when open is false', () => {
    render(
      <ProjectDialog
        open={false}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('should reset form when switching between create and edit mode', async () => {
    const { rerender } = render(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={mockProject}
      />
    )

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Project')).toBeInTheDocument()
    })

    rerender(
      <ProjectDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        project={null}
      />
    )

    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入项目名称')).toHaveValue('')
    })
  })
})
