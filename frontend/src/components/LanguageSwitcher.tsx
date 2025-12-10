import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import client from '@/api/client'

const languages = [
  { code: 'zh', label: '中文' },
  { code: 'en', label: 'English' },
]

export default function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const changeLanguage = async (lang: string) => {
    console.log(`[LanguageSwitcher] Changing language from ${i18n.language} to ${lang}`)

    // 切换前端语言
    await i18n.changeLanguage(lang)
    console.log(`[LanguageSwitcher] i18n language changed to: ${i18n.language}`)

    // 同步到后端设置
    try {
      const response = await client.put(`/settings/language`, { value: lang })
      console.log('[LanguageSwitcher] Backend sync response:', response)
    } catch (error) {
      console.error('Failed to sync language setting to backend:', error)
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <Languages className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => changeLanguage(lang.code)}
            className={i18n.language === lang.code ? 'bg-accent' : ''}
          >
            {lang.label}
            {i18n.language === lang.code && ' ✓'}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
