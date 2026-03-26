'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
          <div className="max-w-md w-full text-center">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mt-4">严重错误</h1>
              <p className="text-gray-600 mt-2">应用遇到了一个严重错误。请刷新页面重试。</p>
            </div>
            <button
              onClick={reset}
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              重试
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
