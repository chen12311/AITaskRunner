import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import './index.css'
import i18n from './i18n' // 初始化 i18n
import router from './router'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ThemeProvider } from './components/ThemeProvider'
import client from './api/client'

// 应用启动时从后端同步语言设置
async function initLanguage() {
  try {
    const response = await client.get<{ key: string; value: string }>('/settings/language')
    const backendLang = response.value

    // 如果后端有设置且与当前不同，则同步
    if (backendLang && backendLang !== i18n.language) {
      console.log(`Syncing language from backend: ${i18n.language} -> ${backendLang}`)
      await i18n.changeLanguage(backendLang)
    }
  } catch {
    console.log('Failed to sync language from backend, using default')
    // 不输出error对象，避免控制台混乱
  }
}

// 先初始化语言，再渲染应用
initLanguage().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ErrorBoundary>
        <ThemeProvider>
          <RouterProvider router={router} />
        </ThemeProvider>
      </ErrorBoundary>
    </StrictMode>,
  )
})
