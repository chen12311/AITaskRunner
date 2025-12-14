/**
 * Sidebar Component Tests
 * 测试 Sidebar 组件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../test-utils'
import userEvent from '@testing-library/user-event'

// Mock sidebar store
const mockClose = vi.fn()
const mockUseSidebarStore = vi.fn()

vi.mock('@/stores', () => ({
  useSidebarStore: () => mockUseSidebarStore(),
}))

describe('Sidebar', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    mockUseSidebarStore.mockReturnValue({
      isOpen: false,
      close: mockClose,
    })
  })

  it('should render sidebar with title', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    render(<Sidebar />)
    expect(screen.getByText('AI Task Runner')).toBeInTheDocument()
    expect(screen.getByText('智能任务管理')).toBeInTheDocument()
  })

  it('should render navigation links', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    render(<Sidebar />)

    expect(screen.getByRole('link', { name: /任务/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /会话/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /日志/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /模板/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /项目/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /设置/ })).toBeInTheDocument()
  })

  it('should render version number', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    render(<Sidebar />)
    expect(screen.getByText('v1.0.0')).toBeInTheDocument()
  })

  it('should have correct navigation paths', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    render(<Sidebar />)

    expect(screen.getByRole('link', { name: /任务/ })).toHaveAttribute('href', '/tasks')
    expect(screen.getByRole('link', { name: /会话/ })).toHaveAttribute('href', '/sessions')
    expect(screen.getByRole('link', { name: /日志/ })).toHaveAttribute('href', '/logs')
    expect(screen.getByRole('link', { name: /模板/ })).toHaveAttribute('href', '/templates')
    expect(screen.getByRole('link', { name: /项目/ })).toHaveAttribute('href', '/projects')
    expect(screen.getByRole('link', { name: /设置/ })).toHaveAttribute('href', '/settings')
  })

  it('should call close when close button is clicked', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    const user = userEvent.setup()
    render(<Sidebar />)

    const closeButton = screen.getByRole('button')
    await user.click(closeButton)

    expect(mockClose).toHaveBeenCalled()
  })

  it('should call close when navigation link is clicked', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    const user = userEvent.setup()
    render(<Sidebar />)

    const tasksLink = screen.getByRole('link', { name: /任务/ })
    await user.click(tasksLink)

    expect(mockClose).toHaveBeenCalled()
  })
})

describe('Sidebar open state', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseSidebarStore.mockReturnValue({
      isOpen: true,
      close: mockClose,
    })
  })

  it('should render with open state when isOpen is true', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    render(<Sidebar />)
    const aside = screen.getByRole('complementary')
    expect(aside).toHaveClass('translate-x-0')
  })

  it('should render overlay when open on mobile', async () => {
    const { default: Sidebar } = await import('@/components/layout/Sidebar')
    render(<Sidebar />)
    // Overlay is present when sidebar is open
    const overlay = document.querySelector('.fixed.inset-0')
    expect(overlay).toBeInTheDocument()
  })
})
