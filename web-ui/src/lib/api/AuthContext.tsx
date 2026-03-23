'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { User } from '@/lib/api/auth'
import {
  getAccessToken,
  getRefreshToken,
  getUser,
  saveUser,
  refreshAccessToken,
  logout as authLogout,
  isAuthenticated,
} from '@/lib/auth'
import { authClient } from '@/lib/api/auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: () => void
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
  updateUser: (user: User) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // 加载用户信息
  const loadUser = useCallback(async () => {
    try {
      const accessToken = getAccessToken()
      if (!accessToken) {
        setUser(null)
        setLoading(false)
        return
      }

      // 从缓存获取用户信息
      const cachedUser = getUser()
      if (cachedUser) {
        setUser(cachedUser)
      }

      // 从API获取最新用户信息
      try {
        const userInfo = await authClient.getCurrentUser(accessToken)
        setUser(userInfo)
        saveUser(userInfo)
      } catch (error: any) {
        // 如果获取失败，尝试刷新令牌
        if (error?.statusCode === 401) {
          console.warn('Token expired, trying to refresh...')
          const newToken = await refreshAccessToken()
          if (newToken) {
            try {
              const userInfo = await authClient.getCurrentUser(newToken)
              setUser(userInfo)
              saveUser(userInfo)
            } catch (err) {
              console.error('Failed to get user info after refresh:', err)
              setUser(null)
            }
          } else {
            // 刷新失败，清除用户信息
            setUser(null)
          }
        } else {
          console.error('Failed to get user info:', error)
          setUser(null)
        }
      }
    } catch (error) {
      console.error('Failed to load user:', error)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  // 初始化加载用户信息
  useEffect(() => {
    loadUser()
  }, [loadUser])

  // 自动刷新令牌
  useEffect(() => {
    if (!isAuthenticated()) return

    const refreshInterval = setInterval(async () => {
      const accessToken = getAccessToken()
      const refreshToken = getRefreshToken()

      if (!accessToken || !refreshToken) return

      try {
        // 检查令牌是否即将过期（在过期前5分钟刷新）
        // 这里简化处理，实际应该解析JWT获取过期时间
        await refreshAccessToken()
      } catch (error) {
        console.error('Auto refresh token failed:', error)
      }
    }, 10 * 60 * 1000) // 每10分钟检查一次

    return () => clearInterval(refreshInterval)
  }, [])

  // 登录（支持用户名密码和SSO）
  const login = useCallback(async (username?: string, password?: string) => {
    if (username && password) {
      // 用户名密码登录
      try {
        setLoading(true)
        const response = await authClient.login(username, password)
        
        // 保存令牌
        setAccessToken(response.access_token)
        setRefreshToken(response.refresh_token)
        saveUser(response.user)
        setUser(response.user)
        
        // 重定向到首页或dashboard
        window.location.href = '/admin/dashboard'
      } catch (error: any) {
        console.error('Login error:', error)
        throw error
      } finally {
        setLoading(false)
      }
    } else {
      // SSO登录
      authClient.initiateSSOLogin()
    }
  }, [])

  // 登出
  const handleLogout = useCallback(async () => {
    setLoading(true)
    try {
      await authLogout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      setLoading(false)
    }
  }, [])

  // 手动刷新令牌
  const refreshToken = useCallback(async (): Promise<boolean> => {
    if (refreshing) return false

    setRefreshing(true)
    try {
      const newToken = await refreshAccessToken()
      if (newToken) {
        // 重新加载用户信息
        await loadUser()
        return true
      }
      return false
    } catch (error) {
      console.error('Refresh token failed:', error)
      return false
    } finally {
      setRefreshing(false)
    }
  }, [loadUser, refreshing])

  // 更新用户信息
  const updateUser = useCallback((newUser: User) => {
    setUser(newUser)
    saveUser(newUser)
  }, [])

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: isAuthenticated(),
    login,
    logout: handleLogout,
    refreshToken,
    updateUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

