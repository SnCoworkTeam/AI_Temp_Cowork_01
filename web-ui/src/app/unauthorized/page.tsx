'use client';

import Link from 'next/link';

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-4">
          <div className="text-6xl mb-4">🔒</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">访问被拒绝</h1>
          <p className="text-gray-600 mb-8">您没有权限访问此页面，请联系管理员获取相应权限</p>
        </div>
        <div className="space-x-4">
          <Link
            href="/admin/dashboard"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            返回仪表板
          </Link>
          <Link
            href="/login"
            className="inline-block px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            重新登录
          </Link>
        </div>
      </div>
    </div>
  );
}
