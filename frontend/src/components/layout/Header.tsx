import { useLocation } from 'react-router-dom'
import { Sun, Moon, Menu, Github } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { useSidebarStore } from '@/stores'
import LanguageSwitcher from '@/components/LanguageSwitcher'

const pageTitleKeys = {
  '/tasks': 'sidebar.nav.tasks',
  '/sessions': 'sidebar.nav.sessions',
  '/logs': 'sidebar.nav.logs',
  '/templates': 'sidebar.nav.templates',
  '/projects': 'sidebar.nav.projects',
  '/settings': 'sidebar.nav.settings',
} as const

export default function Header() {
  const { t } = useTranslation()
  const location = useLocation()
  const { theme, setTheme } = useTheme()
  const { toggle } = useSidebarStore()
  const titleKey = pageTitleKeys[location.pathname as keyof typeof pageTitleKeys]
  const title = titleKey ? t(titleKey) : t('sidebar.title')

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={toggle} className="lg:hidden">
          <Menu className="h-5 w-5" />
        </Button>
        <h1 className="text-lg font-semibold">{title}</h1>
      </div>
      <div className="flex items-center gap-2">
        <LanguageSwitcher />
        <Button variant="ghost" size="icon" asChild>
          <a href="https://github.com/chen12311/AITaskRunner" target="_blank" rel="noopener noreferrer">
            <Github className="h-5 w-5" />
          </a>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={t('header.toggleTheme')}
        >
          {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </Button>
      </div>
    </header>
  )
}
