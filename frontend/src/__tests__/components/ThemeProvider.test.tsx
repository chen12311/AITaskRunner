/**
 * ThemeProvider Component Tests
 * 测试 ThemeProvider 组件
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ThemeProvider } from '@/components/ThemeProvider'

// Mock next-themes
vi.mock('next-themes', () => ({
  ThemeProvider: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => (
    <div data-testid="theme-provider" data-props={JSON.stringify(props)}>
      {children}
    </div>
  ),
}))

describe('ThemeProvider', () => {
  it('should render children', () => {
    render(
      <ThemeProvider>
        <div>Child content</div>
      </ThemeProvider>
    )

    expect(screen.getByText('Child content')).toBeInTheDocument()
  })

  it('should wrap children with NextThemesProvider', () => {
    render(
      <ThemeProvider>
        <div>Wrapped content</div>
      </ThemeProvider>
    )

    expect(screen.getByTestId('theme-provider')).toBeInTheDocument()
  })

  it('should pass correct props to NextThemesProvider', () => {
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    )

    const provider = screen.getByTestId('theme-provider')
    const props = JSON.parse(provider.getAttribute('data-props') || '{}')

    expect(props.attribute).toBe('class')
    expect(props.defaultTheme).toBe('system')
    expect(props.enableSystem).toBe(true)
    expect(props.disableTransitionOnChange).toBe(true)
  })

  it('should render multiple children', () => {
    render(
      <ThemeProvider>
        <div>First child</div>
        <div>Second child</div>
      </ThemeProvider>
    )

    expect(screen.getByText('First child')).toBeInTheDocument()
    expect(screen.getByText('Second child')).toBeInTheDocument()
  })

  it('should render nested components', () => {
    render(
      <ThemeProvider>
        <div>
          <span>Nested content</span>
          <button>Nested button</button>
        </div>
      </ThemeProvider>
    )

    expect(screen.getByText('Nested content')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nested button' })).toBeInTheDocument()
  })
})

describe('ThemeProvider configuration', () => {
  it('should use class attribute for theme', () => {
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    )

    const provider = screen.getByTestId('theme-provider')
    const props = JSON.parse(provider.getAttribute('data-props') || '{}')

    expect(props.attribute).toBe('class')
  })

  it('should enable system theme by default', () => {
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    )

    const provider = screen.getByTestId('theme-provider')
    const props = JSON.parse(provider.getAttribute('data-props') || '{}')

    expect(props.enableSystem).toBe(true)
  })

  it('should default to system theme', () => {
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    )

    const provider = screen.getByTestId('theme-provider')
    const props = JSON.parse(provider.getAttribute('data-props') || '{}')

    expect(props.defaultTheme).toBe('system')
  })

  it('should disable transition on theme change', () => {
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    )

    const provider = screen.getByTestId('theme-provider')
    const props = JSON.parse(provider.getAttribute('data-props') || '{}')

    expect(props.disableTransitionOnChange).toBe(true)
  })
})
