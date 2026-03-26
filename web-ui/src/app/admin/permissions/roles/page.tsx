'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, Edit, Trash2, Search, Shield, X, Key } from 'lucide-react';
import {
  getRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
  addPermissionToRole,
  removePermissionFromRole,
  Role,
  getPermissions,
  Permission,
} from '@/lib/api/admin';

export default function RolesManagementPage() {
  const router = useRouter();
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    permission_ids: [] as string[],
  });

  useEffect(() => {
    loadRoles();
    loadPermissions();
  }, [page, searchTerm]);

  const loadRoles = async () => {
    try {
      setLoading(true);
      const response = await getRoles({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
      });

      console.log('角色列表响应:', response);
      setRoles((response as any).roles || (response as any).items || []);
      setTotal((response as any).total || 0);
    } catch (error) {
      console.error('加载角色列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPermissions = async () => {
    try {
      // 后端API限制page_size最大为100，分页加载
      const response = await getPermissions({ page: 1, page_size: 100 });
      setPermissions((response as any).permissions || (response as any).items || []);
    } catch (error) {
      console.error('加载权限列表失败:', error);
    }
  };

  const handleCreate = async () => {
    // 验证必填字段
    if (!formData.name || !formData.name.trim()) {
      alert('请输入角色名称');
      return;
    }
    if (!formData.code || !formData.code.trim()) {
      alert('请输入角色代码');
      return;
    }

    // 验证角色代码格式（只能是小写字母和下划线，不允许数字）
    const codePattern = /^[a-z_]+$/;
    if (!codePattern.test(formData.code)) {
      alert('角色代码只能包含小写字母和下划线，不能包含数字，例如：project_manager');
      return;
    }

    try {
      const newRole = await createRole({
        name: formData.name.trim(),
        code: formData.code.trim(),
        description: formData.description.trim() || '',
      });

      // 添加权限
      if (newRole.id && formData.permission_ids.length > 0) {
        for (const permissionId of formData.permission_ids) {
          try {
            await addPermissionToRole(newRole.id, permissionId);
          } catch (err) {
            console.error(`添加权限 ${permissionId} 失败:`, err);
          }
        }
      }

      setShowCreateModal(false);
      setFormData({
        name: '',
        code: '',
        description: '',
        permission_ids: [],
      });
      loadRoles();
    } catch (error: any) {
      // 尝试从错误响应中提取详细信息
      let errorMessage = '创建失败';

      // 处理不同的错误格式
      if (error.response) {
        try {
          const errorData = await error.response.json();
          // FastAPI通常返回 {detail: "..."} 或 {detail: [...]}
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              // 如果是验证错误数组，提取所有错误信息
              errorMessage = errorData.detail
                .map((err: any) => {
                  if (typeof err === 'string') return err;
                  return `${err.loc?.join('.') || ''}: ${err.msg || ''}`;
                })
                .join('; ');
            } else {
              errorMessage = errorData.detail;
            }
          } else if (errorData.message) {
            errorMessage = errorData.message;
          } else {
            errorMessage = error.response.statusText || errorMessage;
          }
        } catch {
          errorMessage = error.response.statusText || errorMessage;
        }
      } else if (error.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }

      console.error('创建角色失败:', error);
      alert(`创建失败: ${errorMessage}`);
    }
  };

  const handleEdit = async (role: Role) => {
    try {
      const roleDetail = await getRole(role.id);
      setEditingRole(roleDetail);
      setFormData({
        name: roleDetail.name,
        code: roleDetail.code,
        description: roleDetail.description,
        permission_ids: roleDetail.permissions || [],
      });
      setShowEditModal(true);
    } catch (error) {
      console.error('加载角色详情失败:', error);
      alert('加载角色详情失败');
    }
  };

  const handleUpdate = async () => {
    if (!editingRole) return;

    try {
      await updateRole(editingRole.id, {
        name: formData.name,
        code: formData.code,
        description: formData.description,
      });

      // 更新权限
      const roleDetail = await getRole(editingRole.id);
      const currentPermissionIds = roleDetail.permissions || [];
      const toAdd = formData.permission_ids.filter((id) => !currentPermissionIds.includes(id));
      const toRemove = currentPermissionIds.filter((id) => !formData.permission_ids.includes(id));

      for (const permissionId of toAdd) {
        await addPermissionToRole(editingRole.id, permissionId);
      }
      for (const permissionId of toRemove) {
        await removePermissionFromRole(editingRole.id, permissionId);
      }

      setShowEditModal(false);
      setEditingRole(null);
      loadRoles();
    } catch (error: any) {
      alert(`更新失败: ${error.message || '未知错误'}`);
    }
  };

  const handleDelete = async (role: Role) => {
    if (role.is_system) {
      alert('系统角色不能删除');
      return;
    }
    if (!confirm(`确定要删除角色 "${role.name}" 吗？`)) return;

    try {
      await deleteRole(role.id);
      loadRoles();
    } catch (error: any) {
      alert(`删除失败: ${error.message || '未知错误'}`);
    }
  };

  const handleManagePermissions = async (role: Role) => {
    try {
      const roleDetail = await getRole(role.id);
      setSelectedRole(role);
      setFormData({
        ...formData,
        permission_ids: roleDetail.permissions || [],
      });
      setShowPermissionModal(true);
    } catch (error) {
      console.error('加载角色详情失败:', error);
      alert('加载角色详情失败');
    }
  };

  const handleUpdatePermissions = async () => {
    if (!selectedRole) return;

    try {
      const roleDetail = await getRole(selectedRole.id);
      const currentPermissionIds = roleDetail.permissions || [];
      const toAdd = formData.permission_ids.filter((id) => !currentPermissionIds.includes(id));
      const toRemove = currentPermissionIds.filter((id) => !formData.permission_ids.includes(id));

      for (const permissionId of toAdd) {
        await addPermissionToRole(selectedRole.id, permissionId);
      }
      for (const permissionId of toRemove) {
        await removePermissionFromRole(selectedRole.id, permissionId);
      }

      setShowPermissionModal(false);
      setSelectedRole(null);
      loadRoles();
    } catch (error: any) {
      alert(`更新权限失败: ${error.message || '未知错误'}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            角色管理
          </h1>
          <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
            <Shield className="h-4 w-4" />
            管理系统角色，配置角色权限和角色成员
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              setFormData({
                name: '',
                code: '',
                description: '',
                permission_ids: [],
              });
              setShowCreateModal(true);
            }}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            新建角色
          </button>
        </div>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-5">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="搜索角色..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm bg-gray-50 focus:bg-white"
          />
        </div>
      </div>

      {/* 角色列表 */}
      {loading ? (
        <div className="text-center py-12 bg-white rounded-xl shadow-md border border-gray-200">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      ) : roles.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow-md border border-gray-200">
          <p className="text-gray-600">暂无角色</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    角色名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    角色代码
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    描述
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    权限
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    系统角色
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {roles.map((role) => (
                  <tr key={role.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{role.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{role.code}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500">{role.description || '-'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-2">
                        {role.permissions?.slice(0, 3).map((perm) => (
                          <span
                            key={perm}
                            className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded"
                          >
                            {perm}
                          </span>
                        ))}
                        {role.permissions && role.permissions.length > 3 && (
                          <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                            +{role.permissions.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {role.is_system ? (
                        <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                          是
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                          否
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleManagePermissions(role)}
                          className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                          title="管理权限"
                        >
                          <Key className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(role)}
                          className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                          title="编辑"
                          disabled={role.is_system}
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(role)}
                          className="text-red-600 hover:text-red-900 flex items-center gap-1"
                          title="删除"
                          disabled={role.is_system}
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

      {/* 创建角色模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">新建角色</h2>
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
                    角色名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入角色名称"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    角色代码 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => {
                      // 只允许小写字母和下划线，不允许数字，自动转换
                      const value = e.target.value.toLowerCase().replace(/[^a-z_]/g, '');
                      setFormData({ ...formData, code: value });
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入角色代码（只能包含小写字母和下划线，如：project_manager）"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    只能包含小写字母和下划线，不能包含数字
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="输入角色描述"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">权限</label>
                  <div className="space-y-2 max-h-60 overflow-y-auto border border-gray-300 rounded-lg p-3">
                    {permissions.map((permission) => (
                      <label key={permission.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={formData.permission_ids.includes(permission.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                permission_ids: [...formData.permission_ids, permission.id],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                permission_ids: formData.permission_ids.filter(
                                  (id) => id !== permission.id
                                ),
                              });
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900">{permission.name}</div>
                          <div className="text-xs text-gray-500">
                            {permission.code} ({permission.resource_type}.
                            {permission.permission_type})
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
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

      {/* 编辑角色模态框 */}
      {showEditModal && editingRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">编辑角色</h2>
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingRole(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    角色名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">角色代码</label>
                  <input
                    type="text"
                    value={formData.code}
                    disabled
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">权限</label>
                  <div className="space-y-2 max-h-60 overflow-y-auto border border-gray-300 rounded-lg p-3">
                    {permissions.map((permission) => (
                      <label key={permission.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={formData.permission_ids.includes(permission.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                permission_ids: [...formData.permission_ids, permission.id],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                permission_ids: formData.permission_ids.filter(
                                  (id) => id !== permission.id
                                ),
                              });
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900">{permission.name}</div>
                          <div className="text-xs text-gray-500">
                            {permission.code} ({permission.resource_type}.
                            {permission.permission_type})
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingRole(null);
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

      {/* 管理权限模态框 */}
      {showPermissionModal && selectedRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">管理权限 - {selectedRole.name}</h2>
                <button
                  onClick={() => {
                    setShowPermissionModal(false);
                    setSelectedRole(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-2 max-h-96 overflow-y-auto mb-4">
                {permissions.map((permission) => (
                  <label
                    key={permission.id}
                    className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={formData.permission_ids.includes(permission.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({
                            ...formData,
                            permission_ids: [...formData.permission_ids, permission.id],
                          });
                        } else {
                          setFormData({
                            ...formData,
                            permission_ids: formData.permission_ids.filter(
                              (id) => id !== permission.id
                            ),
                          });
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{permission.name}</div>
                      <div className="text-xs text-gray-500">
                        {permission.code} ({permission.resource_type}.{permission.permission_type})
                      </div>
                    </div>
                  </label>
                ))}
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowPermissionModal(false);
                    setSelectedRole(null);
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdatePermissions}
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
