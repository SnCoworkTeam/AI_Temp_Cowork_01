'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import { Sidebar } from '@/components/Layout/Sidebar';
import { Breadcrumbs } from '@/components/Layout/Breadcrumbs';

export default function ProjectsLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <AuthGuard requireAuth>
      <div className="min-h-screen bg-gray-50">
        {/* 侧边栏 */}
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* 主内容区 */}
        <div className="lg:pl-64">
          {/* 页面内容 */}
          <main className="p-4 sm:p-6 lg:p-8">
            <Breadcrumbs />
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
