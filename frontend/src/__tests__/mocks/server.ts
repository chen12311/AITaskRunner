/**
 * MSW Server Setup - Mock Service Worker
 * 用于测试的 API Mock 服务器
 */
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
