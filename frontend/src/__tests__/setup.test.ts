/**
 * Simple test to verify Vitest configuration
 */
import { describe, it, expect } from 'vitest'

describe('Vitest Setup', () => {
  it('should run basic assertions', () => {
    expect(1 + 1).toBe(2)
  })

  it('should handle string operations', () => {
    expect('hello'.toUpperCase()).toBe('HELLO')
  })

  it('should handle array operations', () => {
    const arr = [1, 2, 3]
    expect(arr).toHaveLength(3)
    expect(arr).toContain(2)
  })

  it('should handle async operations', async () => {
    const result = await Promise.resolve('async result')
    expect(result).toBe('async result')
  })
})
