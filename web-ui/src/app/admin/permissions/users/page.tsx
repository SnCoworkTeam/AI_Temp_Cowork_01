'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, Edit, Trash2, Search, UserPlus, Shield, X, Save, Users } from 'lucide-react';
import {
  getUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser,
  addRoleToUser,
  removeRoleFromUser,
  User,
  UserDetail,
  getRoles,
  Role,
} from '@/lib/api/admin';

export default function UsersManagementPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserDetail | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    display_name: '',
    status: 'active',
    role_ids: [] as string[],
  });

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, [page, searchTerm]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await getUsers({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
      });

      // 处理响应格式：auth-service返回的是 {users: [], total: 0, page: 1, page_size: 20}
      console.log('用户列表响应:', response);
      const usersList = (response as any).users || (response as any).items || [];
      setUsers(usersList);
      setTotal((response as any).total || 0);

      if (usersList.length === 0 && (response as any).total === 0) {
        console.warn('用户列表为空，可能是权限问题或数据库中确实没有用户');
      }
    } catch (error) {
      console.error('加载用户列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRoles = async () => {
    try {
      // 后端API限制page_size最大为100，分页加载
      const response = await getRoles({ page: 1, page_size: 100 });
      setRoles((response as any).roles || (response as any).items || []);
    } catch (error) {
      console.error('加载角色列表失败:', error);
    }
  };

  const handleCreate = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) return;

      const newUser = await createUser({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        display_name: formData.display_name,
        status: formData.status as any,
      });

      if (newUser?.user_id && formData.role_ids.length > 0) {
        for (const roleId of formData.role_ids) {
          try {
            await addRoleToUser(newUser.user_id, roleId);
          } catch (err) {
            console.error(`创建用户后分配角色失败: ${roleId}`, err);
          }
        }
      }

      setShowCreateModal(false);
      setFormData({
        username: '',
        email: '',
        password: '',
        display_name: '',
        status: 'active',
        role_ids: [],
      });
      loadUsers();
    } catch (error: any) {
      alert(`创建失败: ${error.message || '未知错误'}`);
    }
  };

  const handleEdit = async (user: User) => {
    try {
      const userDetail = await getUser(user.user_id);
      setEditingUser(userDetail);
      setFormData({
        username: userDetail.username,
        email: userDetail.email,
        password: '',
        display_name: userDetail.display_name || '',
        status: userDetail.status,
        role_ids: userDetail.role_details?.map((r) => r.id) || [],
      });
      setShowEditModal(true);
    } catch (error) {
      console.error('加载用户详情失败:', error);
      alert('加载用户详情失败');
    }
  };

  const handleUpdate = async () => {
    if (!editingUser) return;

    try {
      const updateData: any = {
        email: formData.email,
        display_name: formData.display_name,
        status: formData.status,
      };
      if (formData.password) {
        updateData.password = formData.password;
      }

      await updateUser(editingUser.user_id, updateData);

      // 更新角色
      const currentRoleIds = editingUser.role_details?.map((r) => r.id) || [];
      const toAdd = formData.role_ids.filter((id) => !currentRoleIds.includes(id));
      const toRemove = currentRoleIds.filter((id) => !formData.role_ids.includes(id));

      for (const roleId of toAdd) {
        await addRoleToUser(editingUser.user_id, roleId);
      }
      for (const roleId of toRemove) {
        await removeRoleFromUser(editingUser.user_id, roleId);
      }

      setShowEditModal(false);
      setEditingUser(null);
      loadUsers();
    } catch (error: any) {
      alert(`更新失败: ${error.message || '未知错误'}`);
    }
  };

  const handleDelete = async (user: User) => {
    if (!confirm(`确定要删除用户 "${user.username}" 吗？`)) return;

    try {
      await deleteUser(user.user_id);
      loadUsers();
    } catch (error: any) {
      alert(`删除失败: ${error.message || '未知错误'}`);
    }
  };

  const handleManageRoles = async (user: User) => {
    try {
      const userDetail = await getUser(user.user_id);
      setSelectedUser(user);
      setFormData({
        ...formData,
        role_ids: userDetail.role_details?.map((r) => r.id) || [],
      });
      setShowRoleModal(true);
    } catch (error) {
      console.error('加载用户详情失败:', error);
      alert('加载用户详情失败');
    }
  };

  const handleUpdateRoles = async () => {
    if (!selectedUser) return;

    try {
      const userDetail = await getUser(selectedUser.user_id);
      const currentRoleIds = userDetail.role_details?.map((r) => r.id) || [];
      const toAdd = formData.role_ids.filter((id) => !currentRoleIds.includes(id));
      const toRemove = currentRoleIds.filter((id) => !formData.role_ids.includes(id));

      for (const roleId of toAdd) {
        await addRoleToUser(selectedUser.user_id, roleId);
      }
      for (const roleId of toRemove) {
        await removeRoleFromUser(selectedUser.user_id, roleId);
      }

      setShowRoleModal(false);
      setSelectedUser(null);
      loadUsers();
    } catch (error: any) {
      alert(`更新角色失败: ${error.message || '未知错误'}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            用户管理
          </h1>
          <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
            <UserPlus className="h-4 w-4" />
            管理系统用户账号，包括创建、编辑、删除用户和分配角色
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              setFormData({
                username: '',
                email: '',
                password: '',
                display_name: '',
                status: 'active',
                role_ids: [],
              });
              setShowCreateModal(true);
            }}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            新建用户
          </button>
        </div>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-5">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="搜索用户..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm bg-gray-50 focus:bg-white"
          />
        </div>
      </div>

      {/* 用户列表 */}
      {loading ? (
        <div className="text-center py-12 bg-white rounded-xl shadow-md border border-gray-200">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow-md border border-gray-200">
          <p className="text-gray-600">暂无用户</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    用户名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    邮箱
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    显示名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    角色
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    状态
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.user_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{user.username}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{user.display_name || '-'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-2">
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
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleManageRoles(user)}
                          className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                          title="管理角色"
                        >
                          <Shield className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(user)}
                          className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                          title="编辑"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(user)}
                          className="text-red-600 hover:text-red-900 flex items-center gap-1"
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 分页 */}
          {total > pageSize && (
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
      )}

      {/* 创建用户模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">新建用户</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    用户名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入用户名"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    邮箱 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入邮箱"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    密码 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    required
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入密码"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">显示名称</label>
                  <input
                    type="text"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入显示名称"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">状态</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="active">活跃</option>
                    <option value="inactive">非活跃</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleCreate}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 编辑用户模态框 */}
      {showEditModal && editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">编辑用户</h2>
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingUser(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                  <input
                    type="text"
                    value={formData.username}
                    disabled
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    邮箱 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    新密码（留空不修改）
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入新密码"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">显示名称</label>
                  <input
                    type="text"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">状态</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="active">活跃</option>
                    <option value="inactive">非活跃</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">角色</label>
                  <div className="space-y-2 max-h-40 overflow-y-auto border border-gray-300 rounded-lg p-3">
                    {roles.map((role) => (
                      <label key={role.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={formData.role_ids.includes(role.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                role_ids: [...formData.role_ids, role.id],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                role_ids: formData.role_ids.filter((id) => id !== role.id),
                              });
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">
                          {role.name} ({role.code})
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingUser(null);
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdate}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  更新
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 管理角色模态框 */}
      {showRoleModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  管理角色 - {selectedUser.username}
                </h2>
                <button
                  onClick={() => {
                    setShowRoleModal(false);
                    setSelectedUser(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto mb-4">
                {roles.map((role) => (
                  <label
                    key={role.id}
                    className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={formData.role_ids.includes(role.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({
                            ...formData,
                            role_ids: [...formData.role_ids, role.id],
                          });
                        } else {
                          setFormData({
                            ...formData,
                            role_ids: formData.role_ids.filter((id) => id !== role.id),
                          });
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{role.name}</div>
                      <div className="text-xs text-gray-500">{role.code}</div>
                    </div>
                  </label>
                ))}
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowRoleModal(false);
                    setSelectedUser(null);
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdateRoles}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
