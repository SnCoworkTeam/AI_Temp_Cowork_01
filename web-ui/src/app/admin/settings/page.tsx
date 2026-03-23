'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authServiceClient } from '@/lib/api/client';

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    display_name: user?.display_name || '',
  });

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || '',
        display_name: user.display_name || '',
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // TODO: 实现用户信息更新API调用
      // await authServiceClient.put(`/users/${user?.user_id}`, formData)

      // 模拟更新
      await new Promise((resolve) => setTimeout(resolve, 500));

      if (updateUser) {
        updateUser({
          ...user!,
          ...formData,
        });
      }

      setMessage({ type: 'success', text: '设置已保存' });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : '保存失败',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">个人设置</h1>
        <p className="text-gray-600 mt-1">管理您的账户信息和偏好设置</p>
      </div>

      {/* 消息提示 */}
      {message && (
        <div
          className={`mb-6 p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <form onSubmit={handleSubmit}>
          <div className="p-6 space-y-6">
            {/* 基本信息 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>
              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="username"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    用户名
                  </label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    邮箱
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label
                    htmlFor="display_name"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    显示名称
                  </label>
                  <input
                    type="text"
                    id="display_name"
                    name="display_name"
                    value={formData.display_name}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="可选"
                  />
                </div>
              </div>
            </div>

            {/* 角色和权限 */}
            {user && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">角色和权限</h2>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">角色</p>
                    <div className="flex flex-wrap gap-2">
                      {user.roles && user.roles.length > 0 ? (
                        user.roles.map((role) => (
                          <span
                            key={role}
                            className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                          >
                            {role}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">无角色</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">权限</p>
                    <div className="flex flex-wrap gap-2">
                      {user.permissions && user.permissions.length > 0 ? (
                        user.permissions.map((permission: string) => (
                          <span
                            key={permission}
                            className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm"
                          >
                            {permission}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">无权限</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 账户信息 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">账户信息</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-2 border-b border-gray-200">
                  <span className="text-gray-600">用户ID</span>
                  <span className="text-gray-900 font-mono">{user?.user_id}</span>
                </div>
                {user?.created_at && (
                  <div className="flex justify-between py-2 border-b border-gray-200">
                    <span className="text-gray-600">注册时间</span>
                    <span className="text-gray-900">
                      {new Date(user.created_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                )}
                {user?.last_login_at && (
                  <div className="flex justify-between py-2">
                    <span className="text-gray-600">最后登录</span>
                    <span className="text-gray-900">
                      {new Date(user.last_login_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 提交按钮 */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '保存中...' : '保存更改'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
