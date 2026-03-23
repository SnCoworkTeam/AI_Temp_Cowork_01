'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { hasRole, hasAnyRole, hasAllRoles } from '@/lib/auth';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireRoles?: string[];
  requireAnyRole?: string[];
  requireAllRoles?: string[];
  redirectTo?: string;
}

export function AuthGuard({
  children,
  requireAuth = true,
  requireRoles,
  requireAnyRole,
  requireAllRoles,
  redirectTo = '/login',
}: AuthGuardProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const router = useRouter();
  const [shouldRender, setShouldRender] = useState(true);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout | null = null;

    // 如果不需要认证，直接允许渲染
    if (!requireAuth) {
      setShouldRender(true);
    } else {
      // 检查是否需要认证（立即检查，确保未登录时快速重定向）
      if (!loading && !isAuthenticated) {
        // 立即重定向到登录页，不显示任何错误信息
        router.push(redirectTo);
        setShouldRender(false);
      } else if (loading && !user) {
        // 如果正在加载，设置超时
        timeoutId = setTimeout(() => {
          // 超时后检查认证状态
          if (!isAuthenticated) {
            router.push(redirectTo);
            setShouldRender(false);
          } else {
            setShouldRender(true);
          }
        }, 1000); // 最多等待1秒
      } else if (user && isAuthenticated) {
        // 检查角色权限
        let hasPermission = true;

        if (requireRoles && !requireRoles.some((role) => hasRole(user, role))) {
          hasPermission = false;
        } else if (requireAnyRole && !hasAnyRole(user, requireAnyRole)) {
          hasPermission = false;
        } else if (requireAllRoles && !hasAllRoles(user, requireAllRoles)) {
          hasPermission = false;
        }

        if (!hasPermission) {
          setTimeout(() => {
            router.push('/unauthorized');
          }, 0);
          setShouldRender(false);
        } else {
          // 权限检查通过，允许渲染
          setShouldRender(true);
        }
      } else if (!loading && !isAuthenticated) {
        // 没有用户且不在加载中，重定向到登录页
        router.push(redirectTo);
        setShouldRender(false);
      }
    }

    // 返回清理函数
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [
    user,
    loading,
    isAuthenticated,
    requireAuth,
    requireRoles,
    requireAnyRole,
    requireAllRoles,
    redirectTo,
    router,
  ]);

  // 如果不需要认证，直接渲染
  if (!requireAuth) {
    return <>{children}</>;
  }

  // 如果需要认证但没有认证，直接返回null（重定向已触发，不显示任何信息）
  if (requireAuth && !isAuthenticated) {
    return null;
  }

  // 如果正在加载且没有用户，返回null（等待认证检查完成）
  if (loading && !user && requireAuth) {
    return null;
  }

  // 如果权限检查未通过，返回null（重定向已触发）
  if (!shouldRender && requireAuth) {
    return null;
  }

  // 其他情况都允许渲染
  return <>{children}</>;
}
