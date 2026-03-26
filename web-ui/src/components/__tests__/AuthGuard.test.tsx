import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/__tests__/test-utils'
import { AuthGuard } from '../AuthGuard'

// Mock the AuthContext
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn()
}))

vi.mock('@/lib/auth', () => ({
  hasRole: vi.fn(),
  hasAnyRole: vi.fn(),
  hasAllRoles: vi.fn()
}))

import { useAuth } from '@/contexts/AuthContext'
import { hasRole, hasAnyRole, hasAllRoles } from '@/lib/auth'

describe('AuthGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render children when not requiring auth', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn()
    })

    render(
      <AuthGuard requireAuth={false}>
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should redirect to login when not authenticated', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn()
    })

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('should render children when authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        fullName: 'Test User',
        status: 'active',
        roles: []
      },
      loading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn()
    })

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should redirect to custom path when specified', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn()
    })

    render(
      <AuthGuard redirectTo="/custom-login">
        <div>Protected Content</div>
      </AuthGuard>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/custom-login')
    })
  })

  it('should check role permissions', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        fullName: 'Test User',
        status: 'active',
        roles: [{ code: 'admin', name: 'Admin' }]
      },
      loading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn()
    })

    vi.mocked(hasRole).mockReturnValue(true)

    render(
      <AuthGuard requireRoles={['admin']}>
        <div>Admin Content</div>
      </AuthGuard>
    )

    expect(screen.getByText('Admin Content')).toBeInTheDocument()
  })

  it('should redirect when user lacks required role', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        fullName: 'Test User',
        status: 'active',
        roles: []
      },
      loading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn()
    })

    vi.mocked(hasRole).mockReturnValue(false)

    render(
      <AuthGuard requireRoles={['admin']}>
        <div>Admin Content</div>
      </AuthGuard>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/unauthorized')
    })
  })

  it('should not render when loading', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: true,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn()
    })

    const { container } = render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    // Should not render content while loading
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})
