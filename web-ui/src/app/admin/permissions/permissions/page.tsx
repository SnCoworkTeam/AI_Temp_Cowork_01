'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, Edit, Trash2, Search, Key, X, Filter } from 'lucide-react';
import {
  getPermissions,
  getPermission,
  createPermission,
  updatePermission,
  deletePermission,
  Permission,
} from '@/lib/api/admin';

export default function PermissionsManagementPage() {
  const router = useRouter();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState('');
  const [permissionTypeFilter, setPermissionTypeFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    resource_type: '',
    permission_type: '',
    description: '',
  });

  useEffect(() => {
    loadPermissions();
  }, [page, searchTerm, resourceTypeFilter, permissionTypeFilter]);

  const loadPermissions = async () => {
    try {
      setLoading(true);
      const response = await getPermissions({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
        resource_type: resourceTypeFilter || undefined,
        permission_type: permissionTypeFilter || undefined,
      });

      console.log('权限列表响应:', response);
      setPermissions((response as any).permissions || (response as any).items || []);
      setTotal((response as any).total || 0);
    } catch (error) {
      console.error('加载权限列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await createPermission({
        name: formData.name,
        code: formData.code,
        resource_type: formData.resource_type,
        permission_type: formData.permission_type,
        description: formData.description,
      });

      setShowCreateModal(false);
      setFormData({
        name: '',
        code: '',
        resource_type: '',
        permission_type: '',
        description: '',
      });
      loadPermissions();
    } catch (error: any) {
      alert(`创建失败: ${error.message || '未知错误'}`);
    }
  };

  const handleEdit = async (permission: Permission) => {
    try {
      const permissionDetail = await getPermission(permission.id);
      setEditingPermission(permissionDetail);
      setFormData({
        name: permissionDetail.name,
        code: permissionDetail.code,
        resource_type: permissionDetail.resource_type,
        permission_type: permissionDetail.permission_type,
        description: permissionDetail.description,
      });
      setShowEditModal(true);
    } catch (error) {
      console.error('加载权限详情失败:', error);
      alert('加载权限详情失败');
    }
  };

  const handleUpdate = async () => {
    if (!editingPermission) return;

    try {
      await updatePermission(editingPermission.id, {
        name: formData.name,
        code: formData.code,
        resource_type: formData.resource_type,
        permission_type: formData.permission_type,
        description: formData.description,
      });

      setShowEditModal(false);
      setEditingPermission(null);
      loadPermissions();
    } catch (error: any) {
      alert(`更新失败: ${error.message || '未知错误'}`);
    }
  };

  const handleDelete = async (permission: Permission) => {
    if (!confirm(`确定要删除权限 "${permission.name}" 吗？`)) return;

    try {
      await deletePermission(permission.id);
      loadPermissions();
    } catch (error: any) {
      alert(`删除失败: ${error.message || '未知错误'}`);
    }
  };

  const resourceTypes = Array.from(new Set(permissions.map((p) => p.resource_type)));
  const permissionTypes = Array.from(new Set(permissions.map((p) => p.permission_type)));

  return (
    <div className="space-y-6">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            权限管理
          </h1>
          <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
            <Key className="h-4 w-4" />
            管理系统权限代码，定义资源访问权限
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              setFormData({
                name: '',
                code: '',
                resource_type: '',
                permission_type: '',
                description: '',
              });
              setShowCreateModal(true);
            }}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            新建权限
          </button>
        </div>
      </div>

      {/* 搜索和过滤栏 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-5">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索权限..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm bg-gray-50 focus:bg-white"
              />
            </div>
          </div>
          <select
            value={resourceTypeFilter}
            onChange={(e) => setResourceTypeFilter(e.target.value)}
            className="px-4 py-2.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm bg-gray-50 focus:bg-white"
          >
            <option value="">全部资源类型</option>
            {resourceTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          <select
            value={permissionTypeFilter}
            onChange={(e) => setPermissionTypeFilter(e.target.value)}
            className="px-4 py-2.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm bg-gray-50 focus:bg-white"
          >
            <option value="">全部权限类型</option>
            {permissionTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 权限列表 */}
      {loading ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      ) : permissions.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-600">暂无权限</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    权限名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    权限代码
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    资源类型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    权限类型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    描述
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {permissions.map((permission) => (
                  <tr key={permission.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{permission.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{permission.code}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded">
                        {permission.resource_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                        {permission.permission_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500">{permission.description || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEdit(permission)}
                          className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                          title="编辑"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(permission)}
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

      {/* 创建权限模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">新建权限</h2>
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
                    权限名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入权限名称"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    权限代码 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        code: e.target.value.toLowerCase().replace(/\s+/g, '_'),
                      })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入权限代码（如：user:read）"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      资源类型 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.resource_type}
                      onChange={(e) => setFormData({ ...formData, resource_type: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="如：user, project"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      权限类型 <span className="text-red-500">*</span>
                    </label>
                    <select
                      required
                      value={formData.permission_type}
                      onChange={(e) =>
                        setFormData({ ...formData, permission_type: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">选择权限类型</option>
                      <option value="read">读取 (read)</option>
                      <option value="write">写入 (write)</option>
                      <option value="delete">删除 (delete)</option>
                      <option value="execute">执行 (execute)</option>
                      <option value="admin">管理 (admin)</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="输入权限描述"
                  />
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

      {/* 编辑权限模态框 */}
      {showEditModal && editingPermission && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">编辑权限</h2>
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingPermission(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    权限名称 <span className="text-red-500">*</span>
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">权限代码</label>
                  <input
                    type="text"
                    value={formData.code}
                    disabled
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      资源类型 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.resource_type}
                      onChange={(e) => setFormData({ ...formData, resource_type: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      权限类型 <span className="text-red-500">*</span>
                    </label>
                    <select
                      required
                      value={formData.permission_type}
                      onChange={(e) =>
                        setFormData({ ...formData, permission_type: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="read">读取 (read)</option>
                      <option value="write">写入 (write)</option>
                      <option value="delete">删除 (delete)</option>
                      <option value="execute">执行 (execute)</option>
                      <option value="admin">管理 (admin)</option>
                    </select>
                  </div>
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
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingPermission(null);
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
    </div>
  );
}
