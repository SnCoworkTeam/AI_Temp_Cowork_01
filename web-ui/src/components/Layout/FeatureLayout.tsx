'use client';

import { useState, ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import { useAuth } from '@/contexts/AuthContext';
import { Menu, X, Home, ChevronRight, LucideIcon } from 'lucide-react';

export interface MenuItem {
  name: string;
  href: string;
  icon?: LucideIcon | string;
  children?: MenuItem[];
}

interface FeatureLayoutProps {
  children: ReactNode;
  title: string;
  description?: string;
  menuItems: MenuItem[];
  backToPortal?: boolean;
}

export function FeatureLayout({
  children,
  title,
  description,
  menuItems,
  backToPortal = true,
}: FeatureLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();

  const toggleExpand = (itemName: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemName)) {
      newExpanded.delete(itemName);
    } else {
      newExpanded.add(itemName);
    }
    setExpandedItems(newExpanded);
  };

  const isActive = (href: string) => {
    return pathname === href || pathname?.startsWith(href + '/');
  };

  const renderMenuItem = (item: MenuItem, level: number = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.name);
    const active = isActive(item.href);
    const Icon = typeof item.icon === 'string' ? null : item.icon;

    return (
      <div key={item.href}>
        <div
          className={`
            flex items-center justify-between px-4 py-2 rounded-lg transition-colors
            ${active ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700 hover:bg-gray-100'}
            ${level > 0 ? 'ml-4' : ''}
          `}
        >
          <Link
            href={item.href}
            className="flex items-center gap-3 flex-1"
            onClick={() => {
              if (!hasChildren) {
                setSidebarOpen(false);
              }
            }}
          >
            {Icon && <Icon className="h-5 w-5" />}
            <span>{item.name}</span>
          </Link>
          {hasChildren && (
            <button
              onClick={(e) => {
                e.preventDefault();
                toggleExpand(item.name);
              }}
              className="p-1 hover:bg-gray-200 rounded"
            >
              <ChevronRight
                className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              />
            </button>
          )}
        </div>
        {hasChildren && isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children!.map((child) => renderMenuItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <AuthGuard requireAuth redirectTo="/login">
      <div className="min-h-screen bg-gray-50 flex">
        {/* 左侧菜单栏 */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-50
            w-64 bg-white border-r border-gray-200
            transform transition-transform duration-300 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            lg:translate-x-0
          `}
        >
          <div className="flex flex-col h-full">
            {/* 菜单头部 */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center gap-2">
                {backToPortal && (
                  <Link
                    href="/portal"
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="返回门户"
                  >
                    <Home className="h-5 w-5 text-gray-600" />
                  </Link>
                )}
                <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* 菜单内容 */}
            <nav className="flex-1 overflow-y-auto p-4 space-y-1">
              {menuItems.map((item) => renderMenuItem(item))}
            </nav>

            {/* 用户信息 */}
            {user && (
              <div className="p-4 border-t border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600 font-semibold text-sm">
                      {user.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{user.username}</p>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* 遮罩层（移动端） */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* 右侧内容区域 */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* 移动端菜单按钮 */}
          <div className="lg:hidden bg-white border-b border-gray-200 px-4 py-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>

          {/* 主内容区 - 直接显示内容，不显示标题和描述 */}
          <main className="flex-1 overflow-y-auto p-4 lg:p-6">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}
