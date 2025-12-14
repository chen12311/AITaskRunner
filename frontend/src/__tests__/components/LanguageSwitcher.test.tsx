/**
 * LanguageSwitcher Component Tests
 * 测试 LanguageSwitcher 组件
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import { I18nextProvider } from 'react-i18next'
import i18n from 'i18next'

// Initialize i18n for testing
i18n.init({
  lng: 'zh',
  fallbackLng: 'zh',
  resources: {
    zh: { translation: {} },
    en: { translation: {} },
  },
})

// Mock API client
vi.mock('@/api/client', () => ({
  default: {
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
  },
}))

const renderWithI18n = (component: React.ReactNode) => {
  return render(
    <I18nextProvider i18n={i18n}>
      {component}
    </I18nextProvider>
  )
}

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    i18n.changeLanguage('zh')
  })

  it('should render language switcher button', () => {
    renderWithI18n(<LanguageSwitcher />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it.skip('should open dropdown menu when clicked', async () => {
    // Skip: Radix UI DropdownMenu doesn't work correctly in jsdom environment
    const user = userEvent.setup()
    renderWithI18n(<LanguageSwitcher />)

    await user.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(screen.getByText('中文')).toBeInTheDocument()
      expect(screen.getByText('English')).toBeInTheDocument()
    })
  })

  it('should show checkmark for current language', async () => {
    const user = userEvent.setup()
    renderWithI18n(<LanguageSwitcher />)

    await user.click(screen.getByRole('button'))

    await waitFor(() => {
      // Current language (zh) should have checkmark
      const zhText = screen.getByText(/中文/)
      expect(zhText).toBeInTheDocument()
    })
  })

  it('should change language when option is clicked', async () => {
    const user = userEvent.setup()
    renderWithI18n(<LanguageSwitcher />)

    await user.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(screen.getByText('English')).toBeInTheDocument()
    })

    await user.click(screen.getByText('English'))

    await waitFor(() => {
      expect(i18n.language).toBe('en')
    })
  })

  it('should sync language to backend', async () => {
    const user = userEvent.setup()
    const client = await import('@/api/client')

    renderWithI18n(<LanguageSwitcher />)

    await user.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(screen.getByText('English')).toBeInTheDocument()
    })

    await user.click(screen.getByText('English'))

    await waitFor(() => {
      expect(client.default.put).toHaveBeenCalledWith('/settings/language', { value: 'en' })
    })
  })

  it('should render language icon', () => {
    renderWithI18n(<LanguageSwitcher />)
    // The Languages icon should be rendered in the button
    const button = screen.getByRole('button')
    expect(button.querySelector('svg')).toBeInTheDocument()
  })
})

describe('LanguageSwitcher dropdown menu', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    i18n.changeLanguage('zh')
  })

  it('should have two language options', async () => {
    const user = userEvent.setup()
    renderWithI18n(<LanguageSwitcher />)

    await user.click(screen.getByRole('button'))

    await waitFor(() => {
      const menuItems = screen.getAllByRole('menuitem')
      expect(menuItems).toHaveLength(2)
    })
  })

  it('should close dropdown after selecting language', async () => {
    const user = userEvent.setup()
    renderWithI18n(<LanguageSwitcher />)

    await user.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(screen.getByText('English')).toBeInTheDocument()
    })

    await user.click(screen.getByText('English'))

    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })
})
