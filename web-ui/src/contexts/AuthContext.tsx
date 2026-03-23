'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User } from '@/lib/api/auth';
import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
  getUser,
  saveUser,
  refreshAccessToken,
  logout as authLogout,
  isAuthenticated,
} from '@/lib/auth';
import { authClient } from '@/lib/api/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username?: string, password?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // 加载用户信息（优化：优先使用缓存，异步更新）
  const loadUser = useCallback(async () => {
    try {
      const accessToken = getAccessToken();
      if (!accessToken) {
        setUser(null);
        setLoading(false);
        return;
      }

      // 优先从缓存获取用户信息，立即显示，不阻塞页面渲染
      const cachedUser = getUser();
      if (cachedUser) {
        setUser(cachedUser);
        setLoading(false); // 立即设置 loading 为 false，不等待 API
      } else {
        // 没有缓存，需要等待 API
        setLoading(true);
      }

      // 异步从API获取最新用户信息（不阻塞UI）
      // 使用更短的超时时间，避免长时间等待
      try {
        const timeoutPromise = new Promise<User>(
          (_, reject) => setTimeout(() => reject(new Error('Request timeout')), 10000) // 增加到10秒
        );

        const userInfoPromise = authClient.getCurrentUser(accessToken);
        const userInfo = await Promise.race([userInfoPromise, timeoutPromise]);

        // 更新用户信息（如果与缓存不同）
        setUser(userInfo);
        saveUser(userInfo);
        // 如果之前没有缓存，现在设置 loading 为 false
        if (!cachedUser) {
          setLoading(false);
        }
      } catch (error: any) {
        // 401 错误时，静默处理，不显示错误日志
        const isUnauthorized =
          error?.statusCode === 401 ||
          error?.message?.includes('401') ||
          error?.message?.includes('Unauthorized');

        if (isUnauthorized) {
          // 如果有缓存用户，先使用缓存，后台尝试刷新
          if (cachedUser) {
            // 后台刷新，不阻塞，静默处理错误
            refreshAccessToken().catch(() => {
              // 刷新失败，静默处理（token 已清除）
            });
            return;
          }

          // 没有缓存，尝试刷新令牌
          try {
            const newToken = await refreshAccessToken();
            if (newToken) {
              try {
                const timeoutPromise = new Promise<User>((_, reject) =>
                  setTimeout(() => reject(new Error('Request timeout')), 3000)
                );
                const userInfoPromise = authClient.getCurrentUser(newToken);
                const userInfo = await Promise.race([userInfoPromise, timeoutPromise]);
                setUser(userInfo);
                saveUser(userInfo);
                setLoading(false);
              } catch (err: any) {
                // 401 错误时，静默处理
                if (err?.statusCode !== 401) {
                  console.error('Failed to get user info after refresh:', err);
                }
                setUser(null);
                setLoading(false);
              }
            } else {
              // Token 刷新失败，清除用户信息
              setUser(null);
              setLoading(false);
            }
          } catch (refreshError) {
            // 401 错误时，静默处理
            if ((refreshError as any)?.statusCode !== 401) {
              console.error('Failed to refresh token:', refreshError);
            }
            setUser(null);
            setLoading(false);
          }
        } else {
          // 其他错误（网络错误、超时等）- 显示错误日志
          console.error('Failed to get user info:', error);
          // 使用缓存或清除
          if (!cachedUser) {
            setUser(null);
            setLoading(false);
          }
          // 如果有缓存，保持使用缓存，不设置 loading
        }
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      setUser(null);
      setLoading(false);
    }
  }, []);

  // 初始化加载用户信息（优化：立即检查缓存，减少初始 loading 时间）
  useEffect(() => {
    let isMounted = true;

    // 立即检查缓存，如果有缓存用户，立即设置 loading 为 false
    const cachedUser = getUser();
    const accessToken = getAccessToken();

    if (cachedUser && accessToken) {
      // 有缓存，立即显示，不等待 API
      setUser(cachedUser);
      setLoading(false);
    }

    // 添加超时保护，确保loading不会一直为true（减少到3秒）
    const timeoutId = setTimeout(() => {
      if (isMounted) {
        console.warn('User loading timeout, setting loading to false');
        setLoading(false);
      }
    }, 3000); // 减少到3秒超时

    // 异步加载最新用户信息（不阻塞）
    loadUser().finally(() => {
      if (isMounted) {
        clearTimeout(timeoutId);
      }
    });

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [loadUser]);

  // 自动刷新令牌
  useEffect(() => {
    if (!isAuthenticated()) return;

    const refreshInterval = setInterval(
      async () => {
        const accessToken = getAccessToken();
        const refreshToken = getRefreshToken();

        if (!accessToken || !refreshToken) return;

        try {
          // 检查令牌是否即将过期（在过期前5分钟刷新）
          // 这里简化处理，实际应该解析JWT获取过期时间
          await refreshAccessToken();
        } catch (error: any) {
          // 401 错误时，静默处理（token 已清除）
          if (error?.statusCode !== 401) {
            console.error('Auto refresh token failed:', error);
          }
        }
      },
      10 * 60 * 1000
    ); // 每10分钟检查一次

    return () => clearInterval(refreshInterval);
  }, []);

  // 登录（支持用户名密码和SSO）
  const login = useCallback(async (username?: string, password?: string) => {
    console.log('=== AuthContext login called ===');
    console.log('Username:', username);
    console.log('Has password:', !!password);

    if (username && password) {
      // 用户名密码登录
      try {
        console.log('Starting login process...');
        setLoading(true);
        console.log('Calling authClient.login...');
        const response = await authClient.login(username, password);
        console.log('Login response received:', {
          hasAccessToken: !!response.access_token,
          hasUser: !!response.user,
          username: response.user?.username,
        });

        // 保存令牌
        setAccessToken(response.access_token);
        setRefreshToken(response.refresh_token);
        saveUser(response.user);
        setUser(response.user);

        console.log('Tokens saved, redirecting...');
        // 重定向到门户页面
        setTimeout(() => {
          window.location.href = '/portal';
        }, 500);
      } catch (error: any) {
        console.error('Login error in AuthContext:', error);
        console.error('Error message:', error?.message);
        console.error('Error stack:', error?.stack);
        throw error;
      } finally {
        setLoading(false);
      }
    } else {
      // SSO登录
      console.log('SSO login initiated');
      authClient.initiateSSOLogin();
    }
  }, []);

  // 登出
  const handleLogout = useCallback(async () => {
    setLoading(true);
    try {
      await authLogout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setLoading(false);
    }
  }, []);

  // 手动刷新令牌
  const refreshToken = useCallback(async (): Promise<boolean> => {
    if (refreshing) return false;

    setRefreshing(true);
    try {
      const newToken = await refreshAccessToken();
      if (newToken) {
        // 重新加载用户信息
        await loadUser();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Refresh token failed:', error);
      return false;
    } finally {
      setRefreshing(false);
    }
  }, [loadUser, refreshing]);

  // 更新用户信息
  const updateUser = useCallback((newUser: User) => {
    setUser(newUser);
    saveUser(newUser);
  }, []);

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: isAuthenticated(),
    login,
    logout: handleLogout,
    refreshToken,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
