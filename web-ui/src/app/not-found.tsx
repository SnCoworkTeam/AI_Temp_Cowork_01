import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-gray-200">404</h1>
          <h2 className="text-3xl font-bold text-gray-900 mt-4">页面未找到</h2>
          <p className="text-gray-600 mt-2">抱歉，您访问的页面不存在或已被移动。</p>
        </div>

        <div className="space-y-4">
          <Link
            href="/"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            返回首页
          </Link>
          <div>
            <Link href="/admin/dashboard" className="text-blue-600 hover:text-blue-700 text-sm">
              前往管理后台
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
