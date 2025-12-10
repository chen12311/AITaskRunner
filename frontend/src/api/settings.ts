import client from './client'
import type { CLIOption, TerminalOption, SettingsMap } from '@/types'

// 后端返回格式: {settings: {key: {value, description}}}
interface SettingsResponse {
  settings: SettingsMap
}

// 后端返回格式: {cli_tools: [...], current: "..."}
interface CLIToolsResponse {
  cli_tools: (CLIOption & { available?: boolean })[]
  current: string
}

// 后端返回格式: {terminals: [...], current: "...", platform: "..."}
interface TerminalsResponse {
  terminals: (TerminalOption & { available?: boolean })[]
  current: string
  platform: string
}

// 优化1.2: localStorage 缓存配置
const SETTINGS_CACHE_KEY = 'aitaskrunner_settings_cache'
const SETTINGS_CACHE_TTL = 5 * 60 * 1000 // 5分钟缓存过期

interface CacheEntry<T> {
  data: T
  timestamp: number
}

function getFromCache<T>(key: string): T | null {
  try {
    const cached = localStorage.getItem(key)
    if (!cached) return null

    const entry: CacheEntry<T> = JSON.parse(cached)
    if (Date.now() - entry.timestamp > SETTINGS_CACHE_TTL) {
      localStorage.removeItem(key)
      return null
    }
    return entry.data
  } catch {
    return null
  }
}

function setToCache<T>(key: string, data: T): void {
  try {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now()
    }
    localStorage.setItem(key, JSON.stringify(entry))
  } catch {
    // 忽略存储错误（如配额超限）
  }
}

export const settingsApi = {
  // 优化1.2: 使用 localStorage 缓存 settings
  async getAllSettings(): Promise<SettingsResponse> {
    // 先检查缓存
    const cached = getFromCache<SettingsResponse>(SETTINGS_CACHE_KEY)
    if (cached) {
      return cached
    }

    // 缓存未命中，请求后端
    const response = await client.get<SettingsResponse>('/settings')
    setToCache(SETTINGS_CACHE_KEY, response)
    return response
  },

  getSetting(key: string): Promise<{ key: string; value: string }> {
    return client.get(`/settings/${key}`)
  },

  async updateSetting(key: string, value: string | number | boolean): Promise<void> {
    await client.put(`/settings/${key}`, { value })
    // 更新后清除缓存，确保下次获取最新数据
    localStorage.removeItem(SETTINGS_CACHE_KEY)
  },

  getAvailableTerminals(): Promise<TerminalsResponse> {
    return client.get('/settings/terminal/available')
  },

  getAvailableCLIs(): Promise<CLIToolsResponse> {
    return client.get('/settings/cli/available')
  },

  getAvailableReviewCLIs(): Promise<CLIToolsResponse> {
    return client.get('/settings/cli/review/available')
  },

  // 手动清除缓存（用于调试或强制刷新）
  clearCache(): void {
    localStorage.removeItem(SETTINGS_CACHE_KEY)
  },
}
