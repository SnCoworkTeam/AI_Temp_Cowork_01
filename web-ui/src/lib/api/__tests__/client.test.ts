import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ApiClient, ApiError } from '../client'

// Mock auth functions
vi.mock('../../auth', () => ({
  getAccessToken: vi.fn(),
  refreshAccessToken: vi.fn()
}))

import { getAccessToken, refreshAccessToken } from '../../auth'

describe('ApiClient', () => {
  let client: ApiClient
  const baseUrl = 'http://test-api.com'

  beforeEach(() => {
    client = new ApiClient(baseUrl)
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('request', () => {
    it('should make a successful GET request', async () => {
      const mockData = { id: 1, name: 'test' }
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockData
      } as Response)

      const result = await client.get('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        `${baseUrl}/test`,
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )
      expect(result).toEqual(mockData)
    })

    it('should include authorization header when token exists', async () => {
      const token = 'test-token'
      vi.mocked(getAccessToken).mockReturnValue(token)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({})
      } as Response)

      await client.get('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${token}`
          })
        })
      )
    })

    it('should handle 401 error and retry with new token', async () => {
      const oldToken = 'old-token'
      const newToken = 'new-token'
      const mockData = { success: true }

      vi.mocked(getAccessToken).mockReturnValue(oldToken)
      vi.mocked(refreshAccessToken).mockResolvedValue(newToken)

      // First call returns 401
      vi.mocked(global.fetch)
        .mockResolvedValueOnce({
          ok: false,
          status: 401
        } as Response)
        // Second call (retry) succeeds
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockData
        } as Response)

      const result = await client.get('/test')

      expect(refreshAccessToken).toHaveBeenCalled()
      expect(global.fetch).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockData)
    })

    it('should redirect to login when token refresh fails', async () => {
      vi.mocked(getAccessToken).mockReturnValue('old-token')
      vi.mocked(refreshAccessToken).mockResolvedValue(null)
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 401
      } as Response)

      // Mock window.location
      const mockLocation = { href: '' }
      Object.defineProperty(window, 'location', {
        writable: true,
        value: mockLocation
      })

      await expect(client.get('/test')).rejects.toThrow('Authentication failed. Please login again.')
      expect(mockLocation.href).toBe('/login')
    })

    it('should handle 429 rate limit error', async () => {
      vi.useFakeTimers()

      const mockData = { success: true }

      // First call returns 429
      vi.mocked(global.fetch)
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          headers: {
            get: () => '2'  // Retry-After: 2 seconds
          }
        } as any)
        // Second call (retry) succeeds
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockData
        } as Response)

      const promise = client.get('/test')

      // Fast-forward time
      await vi.advanceTimersByTimeAsync(2000)

      const result = await promise

      expect(global.fetch).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockData)

      vi.useRealTimers()
    })

    it('should handle 404 error with specific message', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' })
      } as Response)

      await expect(client.get('/test')).rejects.toMatchObject({
        message: 'Resource not found',
        statusCode: 404
      })
    })

    it('should handle generic errors', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' })
      } as Response)

      await expect(client.get('/test')).rejects.toMatchObject({
        message: 'Internal server error',
        statusCode: 500
      })
    })

    it('should handle non-JSON error responses', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Not JSON') }
      } as Response)

      await expect(client.get('/test')).rejects.toMatchObject({
        message: 'HTTP error! status: 500',
        statusCode: 500
      })
    })
  })

  describe('HTTP methods', () => {
    beforeEach(() => {
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true })
      } as Response)
    })

    it('should make POST request with data', async () => {
      const data = { name: 'test', value: 123 }
      await client.post('/test', data)

      expect(global.fetch).toHaveBeenCalledWith(
        `${baseUrl}/test`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data)
        })
      )
    })

    it('should make PUT request with data', async () => {
      const data = { id: 1, name: 'updated' }
      await client.put('/test', data)

      expect(global.fetch).toHaveBeenCalledWith(
        `${baseUrl}/test`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(data)
        })
      )
    })

    it('should make DELETE request', async () => {
      await client.delete('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        `${baseUrl}/test`,
        expect.objectContaining({
          method: 'DELETE'
        })
      )
    })
  })
})
