'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import { Sidebar } from '@/components/Layout/Sidebar';
import { Breadcrumbs } from '@/components/Layout/Breadcrumbs';
import { Home } from 'lucide-react';

export default function ProjectsLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <AuthGuard requireAuth>
      <div className="min-h-screen bg-gray-50">
        {/* 侧边栏 */}
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* 主内容区 */}
        <div className="lg:pl-64">
          {/* 顶部标题栏 */}
          <div className="bg-white border-b border-gray-200 shadow-sm">
            <div className="px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 6h16M4 12h16M4 18h16"
                      />
                    </svg>
                  </button>
                  <img
                    src="/logo.jpg"
                    alt="中化国际"
                    className="h-10 w-auto object-contain"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                  <h1 className="text-2xl font-bold text-gray-900">Lumina AIOS</h1>
                </div>
                <Link
                  href="/portal"
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="返回门户"
                >
                  <Home className="h-5 w-5" />
                  <span className="hidden sm:inline">返回门户</span>
                </Link>
              </div>
            </div>
          </div>

          {/* 页面内容 */}
          <main className="p-4 sm:px-6 lg:px-8">
            <Breadcrumbs />
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
