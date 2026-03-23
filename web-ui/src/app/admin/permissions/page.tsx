'use client';

import Link from 'next/link';
import {
  Users,
  Shield,
  Key,
  Menu,
  ArrowRight,
  UserCheck,
  ShieldCheck,
  KeyRound,
  MenuSquare,
} from 'lucide-react';

const menuItems = [
  {
    name: '用户管理',
    href: '/admin/permissions/users',
    icon: Users,
    description: '管理系统用户账号，包括创建、编辑、删除用户和分配角色',
    color: 'blue',
  },
  {
    name: '角色管理',
    href: '/admin/permissions/roles',
    icon: Shield,
    description: '管理系统角色，配置角色权限和角色成员',
    color: 'green',
  },
  {
    name: '权限管理',
    href: '/admin/permissions/permissions',
    icon: Key,
    description: '管理系统权限代码，定义资源访问权限',
    color: 'purple',
  },
  {
    name: '菜单权限',
    href: '/admin/permissions/menus',
    icon: Menu,
    description: '配置系统菜单项的访问权限，控制菜单可见性',
    color: 'orange',
  },
];

const colorClasses = {
  blue: 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100',
  green: 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100',
  purple: 'bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100',
  orange: 'bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100',
};

const iconColorClasses = {
  blue: 'text-blue-600',
  green: 'text-green-600',
  purple: 'text-purple-600',
  orange: 'text-orange-600',
};

export default function PermissionsPage() {
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">权限管理</h1>
        <p className="text-gray-600 mt-2">
          管理系统用户、角色和权限，包括用户账户、角色分配和权限配置
        </p>
      </div>

      {/* 功能卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block p-6 rounded-lg border-2 transition-all duration-200 ${colorClasses[item.color as keyof typeof colorClasses]} group`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className={`p-2 rounded-lg bg-white ${iconColorClasses[item.color as keyof typeof iconColorClasses]}`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <h2 className="text-xl font-semibold">{item.name}</h2>
                  </div>
                  <p className="text-sm opacity-80 mb-4">{item.description}</p>
                </div>
                <ArrowRight className="w-5 h-5 opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* 快速统计 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">权限管理概览</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <UserCheck className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-blue-600">-</div>
            <div className="text-sm text-gray-600">用户总数</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <ShieldCheck className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-600">-</div>
            <div className="text-sm text-gray-600">角色总数</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <KeyRound className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-purple-600">-</div>
            <div className="text-sm text-gray-600">权限总数</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <MenuSquare className="w-8 h-8 text-orange-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-orange-600">-</div>
            <div className="text-sm text-gray-600">菜单项</div>
          </div>
        </div>
      </div>

      {/* 使用说明 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">使用说明</h3>
        <ul className="text-sm text-blue-800 space-y-2">
          <li className="flex items-start gap-2">
            <span className="font-semibold">1.</span>
            <span>
              <strong>用户管理</strong>：创建和管理系统用户账号，为用户分配角色
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-semibold">2.</span>
            <span>
              <strong>角色管理</strong>：定义系统角色，为角色分配权限
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-semibold">3.</span>
            <span>
              <strong>权限管理</strong>：管理系统权限代码，定义资源访问权限
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-semibold">4.</span>
            <span>
              <strong>菜单权限</strong>：配置菜单项的访问权限，控制不同角色用户可见的菜单
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}
