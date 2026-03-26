import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { authClient, LoginResponse, RegisterResponse, RefreshTokenResponse, User } from '../auth'

describe('AuthClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('register', () => {
    it('should register a new user successfully', async () => {
      const mockResponse: RegisterResponse = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        message: 'User registered successfully'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const result = await authClient.register({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        full_name: 'Test User'
      })

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/register'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle registration error with detail message', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Username already exists' })
      } as Response)

      await expect(authClient.register({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      })).rejects.toThrow('Username already exists')
    })

    it('should handle registration error with message field', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Invalid email format' })
      } as Response)

      await expect(authClient.register({
        username: 'testuser',
        email: 'invalid-email',
        password: 'password123'
      })).rejects.toThrow('Invalid email format')
    })

    it('should handle registration error when response is not JSON', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Not JSON') }
      } as unknown as Response)

      await expect(authClient.register({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      })).rejects.toThrow('注册失败')
    })
  })

  describe('login', () => {
    it('should login successfully', async () => {
      const mockResponse: LoginResponse = {
        access_token: 'access-token-123',
        refresh_token: 'refresh-token-456',
        token_type: 'Bearer',
        expires_in: 3600,
        user: {
          user_id: '123',
          username: 'testuser',
          email: 'test@example.com',
          roles: ['user']
        },
        session_id: 'session-789'
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockResponse
      } as Response)

      const result = await authClient.login('testuser', 'password123')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ username: 'testuser', password: 'password123' })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle login error with detail message', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ detail: 'Invalid credentials' })
      } as Response)

      await expect(authClient.login('testuser', 'wrongpassword'))
        .rejects.toThrow('Invalid credentials')
    })

    it('should handle login error with status code', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => { throw new Error('Not JSON') }
      } as unknown as Response)

      await expect(authClient.login('testuser', 'password123'))
        .rejects.toThrow('登录失败')
    })

    it('should handle network error without message property', async () => {
      const networkError = { name: 'TypeError', toString: () => 'Failed to fetch' }
      vi.mocked(global.fetch).mockRejectedValueOnce(networkError)

      await expect(authClient.login('testuser', 'password123'))
        .rejects.toThrow('网络错误，请检查连接')
    })

    it('should preserve error message when it exists', async () => {
      const customError = new Error('Custom error message')
      vi.mocked(global.fetch).mockRejectedValueOnce(customError)

      await expect(authClient.login('testuser', 'password123'))
        .rejects.toThrow('Custom error message')
    })
  })

  describe('initiateSSOLogin', () => {
    it('should redirect to SSO login page', async () => {
      const mockLocation = { href: '' }
      Object.defineProperty(window, 'location', {
        writable: true,
        value: mockLocation
      })

      await authClient.initiateSSOLogin()

      expect(mockLocation.href).toContain('/sso/login')
    })
  })

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      const mockResponse: RefreshTokenResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse
      } as Response)

      const result = await authClient.refreshToken('old-refresh-token')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/refresh'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ refresh_token: 'old-refresh-token' })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle 401 error with custom error object', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 401
      } as Response)

      try {
        await authClient.refreshToken('expired-token')
        expect.fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toBe('Token refresh failed: Unauthorized')
        expect(error.statusCode).toBe(401)
      }
    })

    it('should handle other errors', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500
      } as Response)

      await expect(authClient.refreshToken('token'))
        .rejects.toThrow('Failed to refresh token')
    })
  })

  describe('getCurrentUser', () => {
    it('should get current user successfully', async () => {
      const mockUser: User = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user', 'admin'],
        display_name: 'Test User',
        permissions: ['read', 'write']
      }

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUser
      } as Response)

      const result = await authClient.getCurrentUser('access-token-123')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/users/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer access-token-123'
          })
        })
      )
      expect(result).toEqual(mockUser)
    })

    it('should handle 401 error', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 401
      } as Response)

      try {
        await authClient.getCurrentUser('invalid-token')
        expect.fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toBe('Unauthorized')
        expect(error.statusCode).toBe(401)
      }
    })

    it('should handle other HTTP errors with detail', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Access denied' })
      } as Response)

      try {
        await authClient.getCurrentUser('token')
        expect.fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toBe('Access denied')
        expect(error.statusCode).toBe(403)
      }
    })

    it('should handle HTTP errors with message field', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ message: 'Server error' })
      } as Response)

      try {
        await authClient.getCurrentUser('token')
        expect.fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toBe('Server error')
        expect(error.statusCode).toBe(500)
      }
    })

    it('should handle non-JSON error response', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Not JSON') }
      } as unknown as Response)

      try {
        await authClient.getCurrentUser('token')
        expect.fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toBe('Failed to get user info')
        expect(error.statusCode).toBe(500)
      }
    })

    it('should handle network error', async () => {
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'))

      try {
        await authClient.getCurrentUser('token')
        expect.fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toBe('网络错误，无法获取用户信息')
        expect(error.statusCode).toBe(0)
      }
    })

    it('should preserve statusCode in caught errors', async () => {
      const errorWithStatus: any = new Error('Auth error')
      errorWithStatus.statusCode = 403
      vi.mocked(global.fetch).mockRejectedValueOnce(errorWithStatus)

      try {
        await authClient.getCurrentUser('token')
        expect.fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toBe('Auth error')
        expect(error.statusCode).toBe(403)
      }
    })
  })

  describe('logout', () => {
    it('should logout successfully', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200
      } as Response)

      await authClient.logout('access-token-123')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/logout'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer access-token-123'
          })
        })
      )
    })

    it('should not throw error even if logout fails', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 500
      } as Response)

      // Logout should not throw error
      await expect(authClient.logout('token')).resolves.toBeUndefined()
    })
  })
})
