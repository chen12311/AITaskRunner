/**
 * Header Component Tests
 * 测试 Header 组件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../test-utils'
import userEvent from '@testing-library/user-event'

// Mock next-themes
const mockSetTheme = vi.fn()
const mockUseTheme = vi.fn()

vi.mock('next-themes', () => ({
  useTheme: () => mockUseTheme(),
}))

// Mock sidebar store
const mockToggle = vi.fn()
vi.mock('@/stores', () => ({
  useSidebarStore: () => ({
    toggle: mockToggle,
  }),
}))

// Mock LanguageSwitcher
vi.mock('@/components/LanguageSwitcher', () => ({
  default: () => <div data-testid="language-switcher">Language Switcher</div>,
}))

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseTheme.mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    })
  })

  it('should render header with title', async () => {
    const { default: Header } = await import('@/components/layout/Header')
    render(<Header />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('should render menu button for mobile', async () => {
    const { default: Header } = await import('@/components/layout/Header')
    render(<Header />)
    const menuButtons = screen.getAllByRole('button')
    expect(menuButtons.length).toBeGreaterThanOrEqual(1)
  })

  it('should render theme toggle button', async () => {
    const { default: Header } = await import('@/components/layout/Header')
    render(<Header />)
    expect(screen.getByLabelText('切换主题')).toBeInTheDocument()
  })

  it('should render language switcher', async () => {
    const { default: Header } = await import('@/components/layout/Header')
    render(<Header />)
    expect(screen.getByTestId('language-switcher')).toBeInTheDocument()
  })

  it('should call toggle when menu button is clicked', async () => {
    const { default: Header } = await import('@/components/layout/Header')
    const user = userEvent.setup()
    render(<Header />)

    // The menu button is the first button with Menu icon
    const menuButton = screen.getAllByRole('button')[0]
    await user.click(menuButton)

    expect(mockToggle).toHaveBeenCalled()
  })

  it('should toggle theme to dark when in light mode', async () => {
    const { default: Header } = await import('@/components/layout/Header')
    const user = userEvent.setup()
    render(<Header />)

    const themeButton = screen.getByLabelText('切换主题')
    await user.click(themeButton)

    expect(mockSetTheme).toHaveBeenCalledWith('dark')
  })

  it('should display page title', async () => {
    const { default: Header } = await import('@/components/layout/Header')
    render(<Header />)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })
})

describe('Header theme toggle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should toggle to light when in dark mode', async () => {
    mockUseTheme.mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    })

    const { default: Header } = await import('@/components/layout/Header')
    const user = userEvent.setup()
    render(<Header />)

    const themeButton = screen.getByLabelText('切换主题')
    await user.click(themeButton)

    expect(mockSetTheme).toHaveBeenCalledWith('light')
  })
})
