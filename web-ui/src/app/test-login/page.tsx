'use client';

import { useState } from 'react';

export default function TestLoginPage() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123456');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const testLogin = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    const authUrl = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://127.0.0.1:8003';
    const loginUrl = `${authUrl}/auth/login`;

    console.log('测试登录:', { username, password: '***', loginUrl });

    try {
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      console.log('响应状态:', response.status, response.statusText);
      console.log('响应头:', Object.fromEntries(response.headers.entries()));

      const data = await response.json();

      if (!response.ok) {
        setError(`登录失败 (${response.status}): ${JSON.stringify(data, null, 2)}`);
        setResult({ status: response.status, error: data });
      } else {
        setResult({ status: response.status, success: true, data });
        // 保存token
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          console.log('Token已保存到localStorage');
        }
      }
    } catch (err: any) {
      console.error('登录错误:', err);
      setError(`网络错误: ${err.message}`);
      setResult({ error: err.message, stack: err.stack });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-6 text-center">登录测试页面</h1>

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Auth Service URL</label>
            <input
              type="text"
              value={process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://127.0.0.1:8003'}
              readOnly
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="admin"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="admin123456"
            />
          </div>
        </div>

        <button
          onClick={testLogin}
          disabled={loading || !username || !password}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? '测试中...' : '测试登录'}
        </button>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm font-medium text-red-800">错误:</p>
            <pre className="text-xs text-red-600 mt-1 whitespace-pre-wrap">{error}</pre>
          </div>
        )}

        {result && (
          <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-md">
            <p className="text-sm font-medium text-gray-800 mb-2">结果:</p>
            <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-auto max-h-96">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-gray-200">
          <h2 className="text-sm font-medium text-gray-700 mb-2">调试信息:</h2>
          <div className="text-xs text-gray-600 space-y-1">
            <p>请打开浏览器控制台 (F12) 查看详细日志</p>
            <p>检查 Network 标签中的请求详情</p>
          </div>
        </div>
      </div>
    </div>
  );
}
