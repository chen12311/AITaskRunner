export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}
