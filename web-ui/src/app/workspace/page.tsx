'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { AuthGuard } from '@/components/AuthGuard';
import {
  Briefcase,
  CheckSquare,
  Bell,
  Star,
  LayoutDashboard,
  MessageSquare,
  Code2,
  ArrowRight,
} from 'lucide-react';

interface QuickLink {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  iconColor: string;
}

const quickLinks: QuickLink[] = [
  {
    title: '待办事项',
    description: '查看并管理你的个人任务',
    href: '/todos',
    icon: CheckSquare,
    color: 'bg-red-50',
    iconColor: 'text-red-600',
  },
  {
    title: '通知中心',
    description: '查看系统消息与项目提醒',
    href: '/notifications',
    icon: Bell,
    color: 'bg-blue-50',
    iconColor: 'text-blue-600',
  },
  {
    title: '收藏夹',
    description: '快速访问常用功能入口',
    href: '/favorites',
    icon: Star,
    color: 'bg-amber-50',
    iconColor: 'text-amber-600',
  },
  {
    title: '项目仪表盘',
    description: '进入项目管理统计总览',
    href: '/projects/dashboard',
    icon: LayoutDashboard,
    color: 'bg-indigo-50',
    iconColor: 'text-indigo-600',
  },
  {
    title: 'AI助手',
    description: '开始新的对话或查看历史',
    href: '/chat',
    icon: MessageSquare,
    color: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
  },
  {
    title: 'OpenCode 开发环境',
    description: '跳转到 OpenCode 进行开发',
    href: '/opencode',
    icon: Code2,
    color: 'bg-purple-50',
    iconColor: 'text-purple-600',
  },
];

export default function WorkspacePage() {
  const { user } = useAuth();

  return (
    <AuthGuard requireAuth>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">个人工作台</h1>
            <p className="text-gray-600 mt-1">集中查看个人工作入口与常用功能</p>
          </div>
          {user && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Briefcase className="h-4 w-4" />
              <span>欢迎，{user.display_name || user.username || '同事'}</span>
            </div>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quickLinks.map((item) => (
            <Link
              key={item.title}
              href={item.href}
              className="group rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div
                    className={`h-10 w-10 rounded-lg ${item.color} flex items-center justify-center`}
                  >
                    <item.icon className={`h-5 w-5 ${item.iconColor}`} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">{item.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{item.description}</p>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-blue-600" />
              </div>
            </Link>
          ))}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">今日概览</h2>
              <p className="text-sm text-gray-500 mt-1">个人动态与近期访问将显示在这里</p>
            </div>
            <span className="text-xs text-gray-400">正在建设中</span>
          </div>
          <div className="mt-4 rounded-lg border border-dashed border-gray-200 bg-gray-50 p-6 text-center text-sm text-gray-500">
            暂无可展示的概览数据，请从上方入口进入相应模块。
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
