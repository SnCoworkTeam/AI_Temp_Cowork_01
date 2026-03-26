'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Bell } from 'lucide-react';

export default function NotificationsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  // 未登录则跳转登录页
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">通知中心</h1>
          <p className="text-gray-600 mt-1">系统通知与待处理消息</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
        <div className="flex flex-col items-center text-center">
          <div className="h-12 w-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
            <Bell className="h-6 w-6" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">暂无通知</h2>
          <p className="text-gray-500 mt-2">当前没有可显示的通知内容</p>
        </div>
      </div>
    </div>
  );
}
