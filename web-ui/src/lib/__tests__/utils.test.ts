import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { cn, debounce, throttle } from '../utils'

describe('utils', () => {
  describe('cn', () => {
    it('should join multiple class names', () => {
      expect(cn('foo', 'bar', 'baz')).toBe('foo bar baz')
    })

    it('should filter out falsy values', () => {
      expect(cn('foo', false, 'bar', null, 'baz', undefined)).toBe('foo bar baz')
    })

    it('should handle empty input', () => {
      expect(cn()).toBe('')
    })

    it('should handle all falsy values', () => {
      expect(cn(false, null, undefined)).toBe('')
    })

    it('should collapse multiple spaces', () => {
      expect(cn('foo  bar', 'baz')).toBe('foo bar baz')
    })

    it('should trim whitespace', () => {
      expect(cn('  foo  ', '  bar  ')).toBe('foo bar')
    })

    it('should handle boolean values', () => {
      const isActive = true
      const isDisabled = false
      expect(cn('button', isActive && 'active', isDisabled && 'disabled')).toBe('button active')
    })
  })

  describe('debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.restoreAllMocks()
    })

    it('should delay function execution', () => {
      const func = vi.fn()
      const debouncedFunc = debounce(func, 100)

      debouncedFunc()
      expect(func).not.toHaveBeenCalled()

      vi.advanceTimersByTime(50)
      expect(func).not.toHaveBeenCalled()

      vi.advanceTimersByTime(50)
      expect(func).toHaveBeenCalledTimes(1)
    })

    it('should cancel previous calls', () => {
      const func = vi.fn()
      const debouncedFunc = debounce(func, 100)

      debouncedFunc()
      vi.advanceTimersByTime(50)
      debouncedFunc()
      vi.advanceTimersByTime(50)
      expect(func).not.toHaveBeenCalled()

      vi.advanceTimersByTime(50)
      expect(func).toHaveBeenCalledTimes(1)
    })

    it('should pass arguments correctly', () => {
      const func = vi.fn()
      const debouncedFunc = debounce(func, 100)

      debouncedFunc('arg1', 'arg2')
      vi.advanceTimersByTime(100)
      expect(func).toHaveBeenCalledWith('arg1', 'arg2')
    })

    it('should use the latest arguments', () => {
      const func = vi.fn()
      const debouncedFunc = debounce(func, 100)

      debouncedFunc('first')
      vi.advanceTimersByTime(50)
      debouncedFunc('second')
      vi.advanceTimersByTime(100)

      expect(func).toHaveBeenCalledTimes(1)
      expect(func).toHaveBeenCalledWith('second')
    })
  })

  describe('throttle', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.restoreAllMocks()
    })

    it('should execute function immediately on first call', () => {
      const func = vi.fn()
      const throttledFunc = throttle(func, 100)

      throttledFunc()
      expect(func).toHaveBeenCalledTimes(1)
    })

    it('should ignore calls within throttle period', () => {
      const func = vi.fn()
      const throttledFunc = throttle(func, 100)

      throttledFunc()
      throttledFunc()
      throttledFunc()
      expect(func).toHaveBeenCalledTimes(1)
    })

    it('should allow execution after throttle period', () => {
      const func = vi.fn()
      const throttledFunc = throttle(func, 100)

      throttledFunc()
      expect(func).toHaveBeenCalledTimes(1)

      vi.advanceTimersByTime(100)
      throttledFunc()
      expect(func).toHaveBeenCalledTimes(2)
    })

    it('should pass arguments correctly', () => {
      const func = vi.fn()
      const throttledFunc = throttle(func, 100)

      throttledFunc('arg1', 'arg2')
      expect(func).toHaveBeenCalledWith('arg1', 'arg2')
    })

    it('should throttle multiple calls correctly', () => {
      const func = vi.fn()
      const throttledFunc = throttle(func, 100)

      // First call - should execute
      throttledFunc('call1')
      expect(func).toHaveBeenCalledTimes(1)
      expect(func).toHaveBeenLastCalledWith('call1')

      // Immediate second call - should be ignored
      throttledFunc('call2')
      expect(func).toHaveBeenCalledTimes(1)

      // Wait for throttle period to pass
      vi.advanceTimersByTime(100)

      // Third call after period - should execute
      throttledFunc('call3')
      expect(func).toHaveBeenCalledTimes(2)
      expect(func).toHaveBeenLastCalledWith('call3')
    })
  })
})
