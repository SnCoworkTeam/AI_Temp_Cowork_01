'use client';

import Link from 'next/link';
import { AuthGuard } from '@/components/AuthGuard';
import { Star, ArrowRight } from 'lucide-react';

export default function FavoritesPage() {
  return (
    <AuthGuard requireAuth>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">收藏夹</h1>
            <p className="text-gray-600 mt-1">管理常用功能入口与个人收藏</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
          <div className="flex flex-col items-center text-center">
            <div className="h-12 w-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mb-4">
              <Star className="h-6 w-6" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">暂无收藏内容</h2>
            <p className="text-gray-500 mt-2">你可以先从门户或工作台进入常用模块</p>
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <Link
                href="/portal"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:border-blue-200 hover:text-blue-600 transition"
              >
                返回门户
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/workspace"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
              >
                前往工作台
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
