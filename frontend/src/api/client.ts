import axios from 'axios'

const isDev = import.meta.env.DEV
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8086'

const client = axios.create({
  baseURL: isDev ? '/api' : `${apiBaseUrl}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

/**
 * 统一提取 API 响应数据
 * 后端可能返回:
 * - 直接数组: [...]
 * - 包装对象: {success: true, data: [...]}
 * - 特殊格式: {sessions: [...]} 或 {settings: {...}}
 */
export function extractData<T>(response: unknown, key?: string): T {
  if (response === null || response === undefined) {
    return [] as unknown as T
  }

  // 如果指定了 key，从对象中提取
  if (key && typeof response === 'object' && key in (response as Record<string, unknown>)) {
    return (response as Record<string, unknown>)[key] as T
  }

  // 如果是 {success, data} 格式
  if (typeof response === 'object' && 'data' in (response as Record<string, unknown>)) {
    return (response as { data: T }).data
  }

  // 直接返回
  return response as T
}

/**
 * 检查 API 操作是否成功
 */
export function isSuccess(response: unknown): boolean {
  if (response === null || response === undefined) {
    return false
  }
  // 如果有 success 字段，检查它
  if (typeof response === 'object' && 'success' in (response as Record<string, unknown>)) {
    return (response as { success: boolean }).success
  }
  // 否则认为成功（后端直接返回数据表示成功）
  return true
}

export default client
