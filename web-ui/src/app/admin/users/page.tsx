'use client';

import { useState, useEffect, FormEvent } from 'react';
import { createUser, deleteUser, getUsers, updateUser, User } from '@/lib/api/admin';

export default function UsersPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [newUsername, setNewUsername] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newDisplayName, setNewDisplayName] = useState('');

  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [editUserId, setEditUserId] = useState<string | null>(null);
  const [editUsername, setEditUsername] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editDisplayName, setEditDisplayName] = useState('');
  const [editStatus, setEditStatus] = useState<'active' | 'inactive'>('active');

  useEffect(() => {
    loadUsers();
  }, [page, searchTerm]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getUsers({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
      });
      const usersList = response.users || (response as any).items || [];
      setUsers(usersList);
      setTotal(response.total || usersList.length);
    } catch (err: any) {
      console.error('Failed to load users:', err);
      setError(err.message || '加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setCreateError(null);
    setNewUsername('');
    setNewEmail('');
    setNewPassword('');
    setNewDisplayName('');
    setIsCreateOpen(true);
  };

  const handleCreateSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (createSubmitting) return;

    try {
      setCreateSubmitting(true);
      setCreateError(null);

      if (!newUsername || !newEmail || !newPassword) {
        setCreateError('用户名、邮箱和密码为必填项');
        return;
      }

      await createUser({
        username: newUsername.trim(),
        email: newEmail.trim(),
        password: newPassword,
        display_name: newDisplayName.trim() || undefined,
        roles: [],
        permissions: [],
        status: 'active',
      });

      setIsCreateOpen(false);
      await loadUsers();
    } catch (err: any) {
      console.error('Failed to create user:', err);
      setCreateError(err.message || '创建用户失败');
    } finally {
      setCreateSubmitting(false);
    }
  };

  const filteredUsers = users.filter(
    (user) =>
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">用户管理</h1>
          <p className="text-gray-600 mt-1">管理系统用户和权限</p>
        </div>
        <button
          type="button"
          onClick={handleOpenCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 添加用户
        </button>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <input
          type="text"
          placeholder="搜索用户..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      )}

      {/* 用户列表 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  用户名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  邮箱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  角色
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    加载中...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    没有找到用户
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.user_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{user.username}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-2">
                        {user.roles.map((role) => (
                          <span
                            key={role}
                            className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded"
                          >
                            {role}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${
                          user.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.status === 'active' ? '活跃' : '非活跃'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        type="button"
                        className="text-blue-600 hover:text-blue-900 mr-4"
                        onClick={() => {
                          setEditError(null);
                          setEditUserId(user.user_id);
                          setEditUsername(user.username);
                          setEditEmail(user.email);
                          setEditDisplayName(user.display_name || '');
                          setEditStatus(user.status === 'active' ? 'active' : 'inactive');
                          setIsEditOpen(true);
                        }}
                      >
                        编辑
                      </button>
                      <button
                        type="button"
                        className="text-red-600 hover:text-red-900"
                        onClick={async () => {
                          if (!window.confirm(`确定要删除用户 ${user.username} 吗？`)) return;
                          try {
                            await deleteUser(user.user_id);
                            await loadUsers();
                          } catch (err: any) {
                            console.error('Failed to delete user:', err);
                            alert(err.message || '删除用户失败');
                          }
                        }}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {!loading && total > pageSize && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              显示 {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} 条，共 {total}{' '}
              条
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                上一页
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * pageSize >= total}
                className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 新建用户弹窗 */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">新建用户</h2>
              <button
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {createError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
                {createError}
              </div>
            )}

            <form className="space-y-4" onSubmit={handleCreateSubmit}>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  用户名<span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="例如：user1"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  邮箱<span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="user@example.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  密码<span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="至少 8 位，包含字母和数字"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">显示名称</label>
                <input
                  type="text"
                  value={newDisplayName}
                  onChange={(e) => setNewDisplayName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="例如：张三"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                  disabled={createSubmitting}
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createSubmitting ? '创建中...' : '确认创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* 编辑用户弹窗 */}
      {isEditOpen && editUserId && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">编辑用户</h2>
              <button
                type="button"
                onClick={() => setIsEditOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {editError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
                {editError}
              </div>
            )}

            <form
              className="space-y-4"
              onSubmit={async (e) => {
                e.preventDefault();
                if (editSubmitting || !editUserId) return;
                try {
                  setEditSubmitting(true);
                  setEditError(null);
                  await updateUser(editUserId, {
                    username: editUsername.trim(),
                    email: editEmail.trim(),
                    display_name: editDisplayName.trim() || undefined,
                    status: editStatus,
                  });
                  setIsEditOpen(false);
                  await loadUsers();
                } catch (err: any) {
                  console.error('Failed to update user:', err);
                  setEditError(err.message || '更新用户失败');
                } finally {
                  setEditSubmitting(false);
                }
              }}
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                <input
                  type="text"
                  value={editUsername}
                  onChange={(e) => setEditUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">显示名称</label>
                <input
                  type="text"
                  value={editDisplayName}
                  onChange={(e) => setEditDisplayName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  value={editStatus}
                  onChange={(e) =>
                    setEditStatus(e.target.value === 'active' ? 'active' : 'inactive')
                  }
                >
                  <option value="active">活跃</option>
                  <option value="inactive">非活跃</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsEditOpen(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                  disabled={editSubmitting}
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {editSubmitting ? '保存中...' : '保存修改'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
