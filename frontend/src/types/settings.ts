export interface SettingItem {
  value: string | number | boolean
  description?: string
}

// 后端返回的设置格式 (key -> {value, description})
export type SettingsMap = Record<string, SettingItem | undefined>

// 简化的设置类型用于页面组件
export interface Settings {
  default_cli?: string
  review_cli?: string
  review_enabled?: boolean
  enable_review?: boolean
  max_concurrent?: number
  terminal_type?: string
  terminal?: string
  max_concurrent_sessions?: number
  watchdog_heartbeat_timeout?: number
  watchdog_check_interval?: number
}

export interface CLIOption {
  id: string
  name: string
  installed: boolean
  recommended?: boolean
  supports_session_recovery?: boolean
  supports_status_check?: boolean
}

export interface TerminalOption {
  id: string
  name: string
  installed: boolean
  recommended?: boolean
}
