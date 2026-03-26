/**
 * 认证工具函数
 */
import { authClient, User, RefreshTokenResponse } from './api/auth'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

/**
 * 获取访问令牌
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  
  // 优先从Cookie获取
  const cookieToken = getCookie(ACCESS_TOKEN_KEY)
  if (cookieToken) return cookieToken
  
  // 从localStorage获取（备用）
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

/**
 * 获取刷新令牌
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  
  // 优先从Cookie获取
  const cookieToken = getCookie(REFRESH_TOKEN_KEY)
  if (cookieToken) return cookieToken
  
  // 从localStorage获取（备用）
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * 设置访问令牌
 */
export function setAccessToken(token: string): void {
  if (typeof window === 'undefined') return
  
  // 设置到localStorage（备用）
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

/**
 * 设置刷新令牌
 */
export function setRefreshToken(token: string): void {
  if (typeof window === 'undefined') return
  
  // 设置到localStorage（备用）
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

/**
 * 清除所有令牌
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return
  
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  
  // 删除Cookie
  deleteCookie(ACCESS_TOKEN_KEY)
  deleteCookie(REFRESH_TOKEN_KEY)
}

/**
 * 保存用户信息
 */
export function saveUser(user: User): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/**
 * 获取用户信息
 */
export function getUser(): User | null {
  if (typeof window === 'undefined') return null
  
  const userStr = localStorage.getItem(USER_KEY)
  if (!userStr) return null
  
  try {
    return JSON.parse(userStr) as User
  } catch {
    return null
  }
}

/**
 * 检查是否已登录
 */
export function isAuthenticated(): boolean {
  return getAccessToken() !== null
}

/**
 * 刷新访问令牌
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return null
  }

  try {
    const response = await authClient.refreshToken(refreshToken)
    setAccessToken(response.access_token)
    setRefreshToken(response.refresh_token)
    return response.access_token
  } catch (error: any) {
    // 401 错误时，静默处理，不显示错误日志
    if (error?.statusCode === 401) {
      // Token 已过期或无效，清除本地存储
      clearTokens()
      return null
    }
    // 其他错误才显示日志
    console.error('Failed to refresh token:', error)
    clearTokens()
    return null
  }
}

/**
 * 登出
 */
export async function logout(): Promise<void> {
  const accessToken = getAccessToken()
  
  if (accessToken) {
    try {
      await authClient.logout(accessToken)
    } catch (error) {
      console.error('Logout error:', error)
    }
  }
  
  clearTokens()
  window.location.href = '/login'
}

/**
 * 从Cookie获取值
 */
function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null
  }
  return null
}

/**
 * 删除Cookie
 */
function deleteCookie(name: string): void {
  if (typeof document === 'undefined') return
  
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
}

/**
 * 检查用户是否有指定角色
 */
export function hasRole(user: User | null, role: string): boolean {
  if (!user) return false
  return user.roles.includes(role)
}

/**
 * 检查用户是否有任一角色
 */
export function hasAnyRole(user: User | null, roles: string[]): boolean {
  if (!user) return false
  return roles.some(role => user.roles.includes(role))
}

/**
 * 检查用户是否有所有角色
 */
export function hasAllRoles(user: User | null, roles: string[]): boolean {
  if (!user) return false
  return roles.every(role => user.roles.includes(role))
}









