/**
 * MainLayout Component Tests
 * 测试 MainLayout 组件
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '../test-utils'
import MainLayout from '@/components/layout/MainLayout'

// Mock Sidebar component
vi.mock('@/components/layout/Sidebar', () => ({
  default: () => <aside data-testid="sidebar">Sidebar</aside>,
}))

// Mock Header component
vi.mock('@/components/layout/Header', () => ({
  default: () => <header data-testid="header">Header</header>,
}))

// Mock Toaster component
vi.mock('@/components/ui/sonner', () => ({
  Toaster: () => <div data-testid="toaster">Toaster</div>,
}))

// Mock react-router-dom Outlet
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    Outlet: () => <div data-testid="outlet">Page Content</div>,
  }
})

describe('MainLayout', () => {
  it('should render layout structure', () => {
    render(<MainLayout />)

    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('header')).toBeInTheDocument()
    expect(screen.getByTestId('outlet')).toBeInTheDocument()
  })

  it('should render Toaster for notifications', () => {
    render(<MainLayout />)
    expect(screen.getByTestId('toaster')).toBeInTheDocument()
  })

  it('should have correct layout structure', () => {
    const { container } = render(<MainLayout />)

    // Main container should have flex layout
    const mainContainer = container.firstChild
    expect(mainContainer).toHaveClass('flex', 'min-h-screen')
  })

  it('should render main content area', () => {
    render(<MainLayout />)

    const main = screen.getByRole('main')
    expect(main).toBeInTheDocument()
    expect(main).toHaveClass('flex-1')
  })

  it('should render content container with flex-1', () => {
    const { container } = render(<MainLayout />)

    const contentContainer = container.querySelector('.flex-1.flex.flex-col')
    expect(contentContainer).toBeInTheDocument()
  })
})

describe('MainLayout responsiveness', () => {
  it('should have proper responsive classes', () => {
    const { container } = render(<MainLayout />)

    const contentContainer = container.querySelector('.lg\\:ml-0')
    expect(contentContainer).toBeInTheDocument()
  })

  it('should have overflow handling on main', () => {
    render(<MainLayout />)

    const main = screen.getByRole('main')
    expect(main).toHaveClass('overflow-auto')
  })

  it('should have background styling on main', () => {
    render(<MainLayout />)

    const main = screen.getByRole('main')
    expect(main).toHaveClass('bg-muted/30')
  })
})
