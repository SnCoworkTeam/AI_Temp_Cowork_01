import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../AuthContext'
import * as authModule from '@/lib/auth'
import * as authClientModule from '@/lib/api/auth'

// Mock auth module
vi.mock('@/lib/auth', () => ({
  getAccessToken: vi.fn(),
  getRefreshToken: vi.fn(),
  setAccessToken: vi.fn(),
  setRefreshToken: vi.fn(),
  getUser: vi.fn(),
  saveUser: vi.fn(),
  refreshAccessToken: vi.fn(),
  logout: vi.fn(),
  isAuthenticated: vi.fn()
}))

// Mock auth client
vi.mock('@/lib/api/auth', () => ({
  authClient: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    initiateSSOLogin: vi.fn()
  }
}))

// Test component that uses the hook
function TestComponent() {
  const auth = useAuth()

  return (
    <div>
      <div data-testid="loading">{auth.loading ? 'loading' : 'loaded'}</div>
      <div data-testid="authenticated">{auth.isAuthenticated ? 'yes' : 'no'}</div>
      <div data-testid="user">{auth.user ? auth.user.username : 'null'}</div>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('useAuth hook', () => {
    it('should throw error when used outside provider', () => {
      // Mock console.error to avoid noise in test output
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(<TestComponent />)
      }).toThrow('useAuth must be used within an AuthProvider')

      consoleError.mockRestore()
    })
  })

  describe('AuthProvider', () => {
    it('should render children', () => {
      vi.mocked(authModule.getAccessToken).mockReturnValue(null)
      vi.mocked(authModule.getUser).mockReturnValue(null)
      vi.mocked(authModule.isAuthenticated).mockReturnValue(false)

      render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      )

      expect(screen.getByText('Test Child')).toBeInTheDocument()
    })

    it('should initialize with no user when no token exists', async () => {
      vi.mocked(authModule.getAccessToken).mockReturnValue(null)
      vi.mocked(authModule.getUser).mockReturnValue(null)
      vi.mocked(authModule.isAuthenticated).mockReturnValue(false)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('loaded')
      })

      expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
      expect(screen.getByTestId('user')).toHaveTextContent('null')
    })

    it('should load cached user on initialization', async () => {
      const mockUser = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user']
      }

      vi.mocked(authModule.getAccessToken).mockReturnValue('mock-token')
      vi.mocked(authModule.getUser).mockReturnValue(mockUser)
      vi.mocked(authModule.isAuthenticated).mockReturnValue(true)
      vi.mocked(authClientModule.authClient.getCurrentUser).mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // Should immediately show cached user
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('testuser')
      })

      expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
    })

    it('should provide updateUser function', async () => {
      const mockUser = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user']
      }

      vi.mocked(authModule.getAccessToken).mockReturnValue(null)
      vi.mocked(authModule.getUser).mockReturnValue(null)
      vi.mocked(authModule.isAuthenticated).mockReturnValue(false)

      function TestUpdateComponent() {
        const auth = useAuth()

        return (
          <div>
            <div data-testid="user">{auth.user ? auth.user.username : 'null'}</div>
            <button onClick={() => auth.updateUser(mockUser)}>Update</button>
          </div>
        )
      }

      render(
        <AuthProvider>
          <TestUpdateComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null')
      })

      // Click update button
      screen.getByRole('button').click()

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('testuser')
      })

      expect(authModule.saveUser).toHaveBeenCalledWith(mockUser)
    })

    it('should set loading to false after initialization', async () => {
      vi.mocked(authModule.getAccessToken).mockReturnValue('mock-token')
      vi.mocked(authModule.getUser).mockReturnValue(null)
      vi.mocked(authModule.isAuthenticated).mockReturnValue(true)

      const mockUser = {
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        roles: ['user']
      }

      // Mock a successful API call
      vi.mocked(authClientModule.authClient.getCurrentUser).mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // Should eventually set loading to false
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('loaded')
      }, { timeout: 2000 })
    })
  })
})
