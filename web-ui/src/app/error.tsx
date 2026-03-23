'use client';

import { useEffect } from 'react';
import Link from 'next/link';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // 记录错误到错误监控服务
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <div className="mb-4">
            <svg
              className="w-24 h-24 mx-auto text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mt-4">出现错误</h1>
          <p className="text-gray-600 mt-2">抱歉，应用遇到了一个错误。请稍后重试。</p>
          {error.digest && <p className="text-xs text-gray-500 mt-2">错误ID: {error.digest}</p>}
        </div>

        <div className="space-y-4">
          <button
            onClick={reset}
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            重试
          </button>
          <div className="space-x-4">
            <Link href="/" className="text-blue-600 hover:text-blue-700 text-sm">
              返回首页
            </Link>
            <span className="text-gray-300">|</span>
            <Link href="/admin/dashboard" className="text-blue-600 hover:text-blue-700 text-sm">
              前往管理后台
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
