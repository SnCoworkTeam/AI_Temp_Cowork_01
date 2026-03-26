'use client';

import { useState } from 'react';

export default function SimpleLoginPage() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123456');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    setMessage('');

    const authUrl = 'http://127.0.0.1:8003';
    const loginUrl = `${authUrl}/auth/login`;

    console.log('=== 开始登录 ===');
    console.log('URL:', loginUrl);
    console.log('用户名:', username);
    console.log('密码长度:', password.length);

    try {
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      console.log('响应状态:', response.status);
      console.log('响应头:', Object.fromEntries(response.headers.entries()));

      const data = await response.json();
      console.log('响应数据:', data);

      if (!response.ok) {
        setError(
          `登录失败 (${response.status}): ${data.detail || data.message || JSON.stringify(data)}`
        );
      } else {
        setMessage('登录成功！');
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          console.log('Token已保存');
          setTimeout(() => {
            window.location.href = '/';
          }, 1000);
        }
      }
    } catch (err: any) {
      console.error('登录错误:', err);
      setError(`网络错误: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold mb-6 text-center">简单登录测试</h1>

        <div className="space-y-4">
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

          <button
            onClick={handleLogin}
            disabled={loading || !username || !password}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? '登录中...' : '登录'}
          </button>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
              {error}
            </div>
          )}

          {message && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm">
              {message}
            </div>
          )}

          <div className="text-xs text-gray-500 mt-4">
            <p>打开浏览器控制台 (F12) 查看详细日志</p>
            <p>API地址: http://127.0.0.1:8003/auth/login</p>
          </div>
        </div>
      </div>
    </div>
  );
}
