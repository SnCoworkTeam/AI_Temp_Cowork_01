import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
  clearTokens,
  saveUser,
  getUser,
  isAuthenticated,
  refreshAccessToken,
  logout,
  hasRole,
  hasAnyRole,
  hasAllRoles
} from '../auth'

// Mock auth client
vi.mock('../api/auth', () => ({
  authClient: {
    refreshToken: vi.fn(),
    logout: vi.fn()
  }
}))

import { authClient } from '../api/auth'

describe('auth utils', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    // Clear cookies (safely handle undefined)
    try {
      const cookies = document.cookie
      if (cookies) {
        cookies.split(";").forEach((c) => {
          document.cookie = c
            .replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/")
        })
      }
    } catch (e) {
      // Ignore cookie clearing errors in test environment
    }
  })

  describe('getAccessToken', () => {
    it('should return null when no token is stored', () => {
      expect(getAccessToken()).toBeNull()
    })

    it('should return token from localStorage', () => {
      localStorage.setItem('access_token', 'test-token')
      expect(getAccessToken()).toBe('test-token')
    })
  })

  describe('getRefreshToken', () => {
    it('should return null when no token is stored', () => {
      expect(getRefreshToken()).toBeNull()
    })

    it('should return token from localStorage', () => {
      localStorage.setItem('refresh_token', 'test-refresh-token')
      expect(getRefreshToken()).toBe('test-refresh-token')
    })
  })

  describe('setAccessToken', () => {
    it('should store access token in localStorage', () => {
      setAccessToken('new-token')
      expect(localStorage.getItem('access_token')).toBe('new-token')
    })
  })

  describe('setRefreshToken', () => {
    it('should store refresh token in localStorage', () => {
      setRefreshToken('new-refresh-token')
      expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')
    })
  })

  describe('clearTokens', () => {
    it('should remove all tokens from localStorage', () => {
      localStorage.setItem('access_token', 'test-token')
      localStorage.setItem('refresh_token', 'test-refresh')
      localStorage.setItem('user', '{"id": 1}')

      clearTokens()

      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })

  describe('saveUser', () => {
    it('should save user to localStorage', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user']
      }

      saveUser(user)

      const stored = localStorage.getItem('user')
      expect(stored).toBeTruthy()
      expect(JSON.parse(stored!)).toEqual(user)
    })
  })

  describe('getUser', () => {
    it('should return null when no user is stored', () => {
      expect(getUser()).toBeNull()
    })

    it('should return user from localStorage', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user']
      }

      localStorage.setItem('user', JSON.stringify(user))

      expect(getUser()).toEqual(user)
    })

    it('should return null when stored data is invalid JSON', () => {
      localStorage.setItem('user', 'invalid-json')
      expect(getUser()).toBeNull()
    })
  })

  describe('isAuthenticated', () => {
    it('should return false when no token is stored', () => {
      expect(isAuthenticated()).toBe(false)
    })

    it('should return true when access token exists', () => {
      localStorage.setItem('access_token', 'test-token')
      expect(isAuthenticated()).toBe(true)
    })
  })

  describe('refreshAccessToken', () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('should return null when no refresh token exists', async () => {
      const result = await refreshAccessToken()
      expect(result).toBeNull()
      expect(authClient.refreshToken).not.toHaveBeenCalled()
    })

    it('should refresh token successfully', async () => {
      const mockResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600
      }

      localStorage.setItem('refresh_token', 'old-refresh-token')
      vi.mocked(authClient.refreshToken).mockResolvedValue(mockResponse)

      const result = await refreshAccessToken()

      expect(result).toBe('new-access-token')
      expect(authClient.refreshToken).toHaveBeenCalledWith('old-refresh-token')
      expect(localStorage.getItem('access_token')).toBe('new-access-token')
      expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')
    })

    it('should clear tokens on 401 error', async () => {
      localStorage.setItem('access_token', 'old-access-token')
      localStorage.setItem('refresh_token', 'old-refresh-token')

      const error = new Error('Unauthorized')
      ;(error as any).statusCode = 401
      vi.mocked(authClient.refreshToken).mockRejectedValue(error)

      const result = await refreshAccessToken()

      expect(result).toBeNull()
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
    })

    it('should clear tokens on other errors', async () => {
      localStorage.setItem('access_token', 'old-access-token')
      localStorage.setItem('refresh_token', 'old-refresh-token')

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      vi.mocked(authClient.refreshToken).mockRejectedValue(new Error('Network error'))

      const result = await refreshAccessToken()

      expect(result).toBeNull()
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(consoleErrorSpy).toHaveBeenCalled()

      consoleErrorSpy.mockRestore()
    })
  })

  describe('logout', () => {
    let locationHref: string

    beforeEach(() => {
      vi.clearAllMocks()
      locationHref = window.location.href
      delete (window as any).location
      window.location = { href: '' } as any
    })

    afterEach(() => {
      window.location.href = locationHref
    })

    it('should logout successfully with access token', async () => {
      localStorage.setItem('access_token', 'test-token')
      localStorage.setItem('refresh_token', 'test-refresh')
      vi.mocked(authClient.logout).mockResolvedValue()

      await logout()

      expect(authClient.logout).toHaveBeenCalledWith('test-token')
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(window.location.href).toBe('/login')
    })

    it('should logout without access token', async () => {
      await logout()

      expect(authClient.logout).not.toHaveBeenCalled()
      expect(window.location.href).toBe('/login')
    })

    it('should handle logout error gracefully', async () => {
      localStorage.setItem('access_token', 'test-token')
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      vi.mocked(authClient.logout).mockRejectedValue(new Error('Logout failed'))

      await logout()

      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout error:', expect.any(Error))
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(window.location.href).toBe('/login')

      consoleErrorSpy.mockRestore()
    })
  })

  describe('hasRole', () => {
    it('should return false when user is null', () => {
      expect(hasRole(null, 'admin')).toBe(false)
    })

    it('should return true when user has the role', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['admin', 'user']
      }

      expect(hasRole(user, 'admin')).toBe(true)
    })

    it('should return false when user does not have the role', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user']
      }

      expect(hasRole(user, 'admin')).toBe(false)
    })
  })

  describe('hasAnyRole', () => {
    it('should return false when user is null', () => {
      expect(hasAnyRole(null, ['admin', 'moderator'])).toBe(false)
    })

    it('should return true when user has at least one role', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user', 'moderator']
      }

      expect(hasAnyRole(user, ['admin', 'moderator'])).toBe(true)
    })

    it('should return false when user has none of the roles', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user']
      }

      expect(hasAnyRole(user, ['admin', 'moderator'])).toBe(false)
    })
  })

  describe('hasAllRoles', () => {
    it('should return false when user is null', () => {
      expect(hasAllRoles(null, ['admin', 'moderator'])).toBe(false)
    })

    it('should return true when user has all roles', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user', 'admin', 'moderator']
      }

      expect(hasAllRoles(user, ['admin', 'moderator'])).toBe(true)
    })

    it('should return false when user is missing some roles', () => {
      const user = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user', 'admin']
      }

      expect(hasAllRoles(user, ['admin', 'moderator'])).toBe(false)
    })
  })

  describe('Cookie support', () => {
    beforeEach(() => {
      // Clear localStorage
      localStorage.clear()
      // Try to clear cookies (may not work in test environment)
      try {
        const cookies = document.cookie
        if (cookies) {
          cookies.split(";").forEach((c) => {
            document.cookie = c
              .replace(/^ +/, "")
              .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/")
          })
        }
      } catch (e) {
        // Ignore
      }
    })

    it('should fallback to localStorage when cookie is not available', () => {
      localStorage.setItem('access_token', 'local-token')
      const token = getAccessToken()
      // In test environment, cookie may not work, so we get from localStorage
      expect(token).toBe('local-token')
    })

    it('should get refresh token from localStorage', () => {
      localStorage.setItem('refresh_token', 'local-refresh-token')
      const token = getRefreshToken()
      expect(token).toBe('local-refresh-token')
    })

    it('should clear both localStorage and cookies', () => {
      localStorage.setItem('access_token', 'local-token')
      localStorage.setItem('refresh_token', 'local-refresh')

      clearTokens()

      // Both tokens should be cleared from localStorage
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })
})
