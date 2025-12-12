import { NavLink } from 'react-router-dom'
import { ListTodo, Activity, FileText, FileCode, FolderOpen, Settings, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { useSidebarStore } from '@/stores'

const navItems = [
  { path: '/tasks', labelKey: 'sidebar.nav.tasks', icon: ListTodo },
  { path: '/sessions', labelKey: 'sidebar.nav.sessions', icon: Activity },
  { path: '/logs', labelKey: 'sidebar.nav.logs', icon: FileText },
  { path: '/templates', labelKey: 'sidebar.nav.templates', icon: FileCode },
  { path: '/projects', labelKey: 'sidebar.nav.projects', icon: FolderOpen },
  { path: '/settings', labelKey: 'sidebar.nav.settings', icon: Settings },
] as const

export default function Sidebar() {
  const { t } = useTranslation()
  const { isOpen, close } = useSidebarStore()

  return (
    <>
      {/* 移动端遮罩层 */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={close} />
      )}

      <aside className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 bg-sidebar text-sidebar-foreground flex flex-col h-screen transition-transform lg:translate-x-0 border-r border-sidebar-border',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="p-4 border-b border-sidebar-border flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">{t('sidebar.title')}</h1>
            <p className="text-xs text-muted-foreground mt-1">{t('sidebar.subtitle')}</p>
          </div>
          <button onClick={close} className="lg:hidden p-1 hover:bg-sidebar-accent rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={close}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 text-sm transition-colors',
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground border-r-2 border-sidebar-primary'
                    : 'text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                )
              }
            >
              <item.icon className="h-5 w-5" />
              {t(item.labelKey)}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-sidebar-border text-xs text-muted-foreground">
          v1.0.0
        </div>
      </aside>
    </>
  )
}
