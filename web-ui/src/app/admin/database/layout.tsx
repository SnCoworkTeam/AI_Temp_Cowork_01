'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import {
  Database,
  Table as TableIcon,
  HardDrive,
  Activity,
  ChevronRight,
  Home,
} from 'lucide-react';

interface DatabaseLayoutProps {
  children: React.ReactNode;
}

const navigation = [
  {
    name: '概览',
    href: '/admin/database/overview',
    icon: Database,
  },
  {
    name: '数据表',
    href: '/admin/database/tables',
    icon: TableIcon,
  },
  {
    name: '备份管理',
    href: '/admin/database/backups',
    icon: HardDrive,
  },
  {
    name: '性能监控',
    href: '/admin/database/performance',
    icon: Activity,
  },
];

export default function DatabaseLayout({ children }: DatabaseLayoutProps) {
  const pathname = usePathname();

  return (
    <AuthGuard requireAuth requireRoles={['admin']}>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
        {/* 侧边栏 */}
        <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
          <div className="p-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">数据库管理</h2>
            <nav className="space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`
                      flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors
                      ${
                        isActive
                          ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    <span>{item.name}</span>
                    {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
                  </Link>
                );
              })}
            </nav>
          </div>
        </aside>

        {/* 主内容区 */}
        <main className="flex-1 overflow-y-auto">
          {/* 顶部标题栏 */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="container mx-auto px-6 py-4">
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据库管理</h1>
                <Link
                  href="/portal"
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                  title="返回门户"
                >
                  <Home className="h-5 w-5" />
                  <span className="hidden sm:inline">返回门户</span>
                </Link>
              </div>
            </div>
          </div>
          <div className="container mx-auto px-6 py-8">{children}</div>
        </main>
      </div>
    </AuthGuard>
  );
}
