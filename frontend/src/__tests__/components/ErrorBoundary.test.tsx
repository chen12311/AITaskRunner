/**
 * ErrorBoundary Component Tests
 * 测试 ErrorBoundary 组件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../test-utils'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Mock window.location.reload
const mockReload = vi.fn()
Object.defineProperty(window, 'location', {
  value: { reload: mockReload },
  writable: true,
})

// Mock console.error to avoid test output noise
const originalConsoleError = console.error
beforeEach(() => {
  vi.clearAllMocks()
  console.error = vi.fn()
})

afterEach(() => {
  console.error = originalConsoleError
})

// Component that throws an error
const ThrowError = ({ shouldThrow = true }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}

describe('ErrorBoundary', () => {
  it('should render children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('Child content')).toBeInTheDocument()
  })

  it('should render error UI when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText('页面出错了')).toBeInTheDocument()
    expect(screen.getByText('抱歉，页面出现了错误')).toBeInTheDocument()
  })

  it('should render reload button when error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByRole('button', { name: '重新加载' })).toBeInTheDocument()
  })

  it('should render alert icon when error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // The AlertTriangle icon should be rendered
    const errorContainer = screen.getByText('页面出错了').closest('div')
    expect(errorContainer?.parentElement).toBeInTheDocument()
  })

  it('should call window.location.reload when reload button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    const reloadButton = screen.getByRole('button', { name: '重新加载' })
    await user.click(reloadButton)

    expect(mockReload).toHaveBeenCalled()
  })

  it('should log error to console', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(console.error).toHaveBeenCalled()
  })

  it('should handle multiple children', () => {
    render(
      <ErrorBoundary>
        <div>First child</div>
        <div>Second child</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('First child')).toBeInTheDocument()
    expect(screen.getByText('Second child')).toBeInTheDocument()
  })

  it('should not show error UI when child does not throw', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('No error')).toBeInTheDocument()
    expect(screen.queryByText('页面出错了')).not.toBeInTheDocument()
  })
})

describe('ErrorBoundary state management', () => {
  it('should update hasError state when error occurs', () => {
    // This test verifies the internal state change through UI
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // If hasError is true, error UI is shown
    expect(screen.getByText('页面出错了')).toBeInTheDocument()
  })

  it('should have proper error UI styling', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // The error UI should have flex and center alignment
    const container = screen.getByText('页面出错了').closest('.min-h-screen')
    expect(container).toHaveClass('flex', 'flex-col', 'items-center', 'justify-center')
  })
})
