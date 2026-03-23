'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiGatewayClient } from '@/lib/api/client';

interface BasicDataCategory {
  id: string;
  category_type: string;
  code: string;
  name: string;
  description?: string;
  parent_id?: string;
  sort_order: number;
  is_active: boolean;
  metadata?: any;
  created_at: string;
  updated_at: string;
}

export default function BasicDataPage() {
  const [categories, setCategories] = useState<BasicDataCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<BasicDataCategory | null>(null);
  const [editingType, setEditingType] = useState<string | null>(null);
  const [newTypeName, setNewTypeName] = useState('');
  const [showDeleteTypeConfirm, setShowDeleteTypeConfirm] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    category_type: '',
    code: '',
    name: '',
    description: '',
    parent_id: '',
    sort_order: 0,
    is_active: true,
  });

  // 获取分类列表
  const fetchCategories = async () => {
    try {
      setLoading(true);
      let url = '/api/v1/basic-data/categories';
      const params = new URLSearchParams();
      if (filterType) {
        params.append('category_type', filterType);
      }
      if (params.toString()) {
        url += '?' + params.toString();
      }
      const data = await apiGatewayClient.get<any>(url);
      // API可能返回数组或对象，需要兼容处理
      if (Array.isArray(data)) {
        setCategories(data);
      } else if (data.items && Array.isArray(data.items)) {
        setCategories(data.items);
      } else {
        setCategories([]);
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || '获取分类列表失败');
      console.error('获取分类列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, [filterType]);

  // 创建分类
  const handleCreate = async () => {
    try {
      const payload: any = {
        category_type: formData.category_type,
        code: formData.code,
        name: formData.name,
        description: formData.description || undefined,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
      };

      if (formData.parent_id) {
        payload.parent_id = formData.parent_id;
      }

      await apiGatewayClient.post('/api/v1/basic-data/categories', payload);

      setShowCreateModal(false);
      setFormData({
        category_type: '',
        code: '',
        name: '',
        description: '',
        parent_id: '',
        sort_order: 0,
        is_active: true,
      });
      fetchCategories();
    } catch (err: any) {
      alert(err.message || '创建失败');
      console.error('创建分类失败:', err);
    }
  };

  // 更新分类
  const handleUpdate = async () => {
    if (!editingCategory) return;

    try {
      const payload: any = {
        category_type: formData.category_type, // 确保更新时保留 category_type
        code: formData.code,
        name: formData.name,
        description: formData.description || undefined,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
      };

      if (formData.parent_id) {
        payload.parent_id = formData.parent_id;
      }

      await apiGatewayClient.put(`/api/v1/basic-data/categories/${editingCategory.id}`, payload);

      setShowCreateModal(false);
      setEditingCategory(null);
      setFormData({
        category_type: '',
        code: '',
        name: '',
        description: '',
        parent_id: '',
        sort_order: 0,
        is_active: true,
      });
      fetchCategories();
    } catch (err: any) {
      alert(err.message || '更新失败');
      console.error('更新分类失败:', err);
    }
  };

  // 删除分类
  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个分类吗？')) {
      return;
    }

    try {
      await apiGatewayClient.delete(`/api/v1/basic-data/categories/${id}`);

      fetchCategories();
    } catch (err: any) {
      alert(err.message || '删除失败');
      console.error('删除分类失败:', err);
    }
  };

  // 编辑分类
  const handleEdit = (category: BasicDataCategory) => {
    setEditingCategory(category);
    setFormData({
      category_type: category.category_type,
      code: category.code,
      name: category.name,
      description: category.description || '',
      parent_id: category.parent_id || '',
      sort_order: category.sort_order,
      is_active: category.is_active,
    });
    setShowCreateModal(true);
  };

  // 重命名分类类型
  const handleRenameType = async (oldType: string, newType: string) => {
    if (!newType || newType.trim() === '') {
      alert('分类类型名称不能为空');
      return;
    }

    if (
      !confirm(
        `确定要将分类类型 "${oldType}" 重命名为 "${newType}" 吗？这将更新该类型下的所有分类项。`
      )
    ) {
      return;
    }

    try {
      // 获取该类型下的所有分类
      const typeCategories = categories.filter((c) => c.category_type === oldType);

      // 批量更新每个分类的 category_type
      for (const category of typeCategories) {
        await apiGatewayClient.put(`/api/v1/basic-data/categories/${category.id}`, {
          category_type: newType,
          code: category.code,
          name: category.name,
          description: category.description || undefined,
          sort_order: category.sort_order,
          is_active: category.is_active,
        });
      }

      setEditingType(null);
      setNewTypeName('');
      fetchCategories();
      alert('分类类型重命名成功');
    } catch (err: any) {
      alert(err.message || '重命名失败');
      console.error('重命名分类类型失败:', err);
    }
  };

  // 删除整个分类类型及其所有子项
  const handleDeleteType = async (type: string) => {
    const typeCategories = categories.filter((c) => c.category_type === type);
    const count = typeCategories.length;

    if (!confirm(`确定要删除分类类型 "${type}" 及其下的 ${count} 个分类项吗？此操作不可恢复！`)) {
      return;
    }

    try {
      // 批量删除该类型下的所有分类
      let deletedCount = 0;
      let errorCount = 0;

      for (const category of typeCategories) {
        try {
          await apiGatewayClient.delete(`/api/v1/basic-data/categories/${category.id}`);
          deletedCount++;
        } catch (err) {
          errorCount++;
          console.error(`删除分类 ${category.code} 失败:`, err);
        }
      }

      setShowDeleteTypeConfirm(null);
      fetchCategories();

      if (errorCount > 0) {
        alert(`删除了 ${deletedCount} 个分类，${errorCount} 个分类删除失败（可能有关联的项目）`);
      } else {
        alert(`成功删除分类类型 "${type}" 及其下的 ${deletedCount} 个分类项`);
      }
    } catch (err: any) {
      alert(err.message || '删除失败');
      console.error('删除分类类型失败:', err);
      setShowDeleteTypeConfirm(null);
    }
  };

  // 获取分类类型列表
  const categoryTypes = Array.from(new Set(categories.map((c) => c.category_type)));

  // 分类类型的中文名称映射
  const categoryTypeNames: Record<string, string> = {
    industry_chain: '产业链',
    production_base: '生产基地/业务单元',
    project_phase: '项目阶段',
    phase_status: '阶段状态',
    application_domain: '应用领域',
    project_category: '项目分类',
  };

  // 按类型分组
  const categoriesByType = categoryTypes.reduce(
    (acc, type) => {
      acc[type] = categories.filter((c) => c.category_type === type);
      return acc;
    },
    {} as Record<string, BasicDataCategory[]>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">基础数据维护</h1>
          <p className="mt-2 text-gray-600">管理项目分类、行业、领域等基础数据</p>
        </div>
        <button
          onClick={() => {
            setEditingCategory(null);
            setFormData({
              category_type: '',
              code: '',
              name: '',
              description: '',
              parent_id: '',
              sort_order: 0,
              is_active: true,
            });
            setShowCreateModal(true);
          }}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          + 新建分类
        </button>
      </div>

      {/* 过滤器 */}
      <div className="mb-6 flex gap-4">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="rounded-lg border border-gray-300 px-4 py-2"
        >
          <option value="">全部类型</option>
          {categoryTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      {/* 错误提示 */}
      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-700">{error}</div>}

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      )}

      {/* 分类列表 */}
      {!loading && (
        <div className="space-y-6">
          {categoryTypes.map((type) => (
            <div key={type} className="rounded-lg border border-gray-200 bg-white p-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {editingType === type ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={newTypeName}
                        onChange={(e) => setNewTypeName(e.target.value)}
                        className="rounded-lg border border-gray-300 px-3 py-1.5 text-xl font-semibold focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="新分类类型名称"
                        autoFocus
                      />
                      <button
                        onClick={() => {
                          handleRenameType(type, newTypeName);
                        }}
                        className="rounded-lg bg-green-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-700 transition-colors"
                      >
                        保存
                      </button>
                      <button
                        onClick={() => {
                          setEditingType(null);
                          setNewTypeName('');
                        }}
                        className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        取消
                      </button>
                    </div>
                  ) : (
                    <h2 className="text-xl font-semibold text-gray-900">
                      {categoryTypeNames[type] || type}
                    </h2>
                  )}
                  <span className="text-sm text-gray-500">
                    ({categoriesByType[type].length} 项)
                  </span>
                </div>
                {editingType !== type && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setEditingType(type);
                        setNewTypeName(type);
                      }}
                      className="rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
                      title="重命名分类类型"
                    >
                      重命名类型
                    </button>
                    <button
                      onClick={() => setShowDeleteTypeConfirm(type)}
                      className="rounded-lg bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100 transition-colors"
                      title="删除整个分类类型及其所有子项"
                    >
                      删除类型
                    </button>
                  </div>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        编码
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        名称
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        描述
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        排序
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        状态
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoriesByType[type].map((category) => (
                      <tr key={category.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900">{category.code}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{category.name}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {category.description || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">{category.sort_order}</td>
                        <td className="px-4 py-3 text-sm">
                          <span
                            className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                              category.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {category.is_active ? '启用' : '禁用'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleEdit(category)}
                              className="rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
                            >
                              编辑
                            </button>
                            <button
                              onClick={() => handleDelete(category.id)}
                              className="rounded-lg bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100 transition-colors"
                            >
                              删除
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}

          {categoryTypes.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
              <p className="text-gray-600">暂无分类数据</p>
            </div>
          )}
        </div>
      )}

      {/* 创建/编辑模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-2xl rounded-xl bg-white shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  {editingCategory ? '编辑分类' : '新建分类'}
                </h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingCategory(null);
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">分类类型 *</label>
                  <input
                    type="text"
                    value={formData.category_type}
                    onChange={(e) => setFormData({ ...formData, category_type: e.target.value })}
                    disabled={!!editingCategory}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    placeholder="如：project_type, industry, domain"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">编码 *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    placeholder="分类编码"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">名称 *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    placeholder="分类名称"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    rows={3}
                    placeholder="分类描述"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">排序顺序</label>
                    <input
                      type="number"
                      value={formData.sort_order}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          sort_order: parseInt(e.target.value) || 0,
                        })
                      }
                      className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">状态</label>
                    <select
                      value={formData.is_active ? 'true' : 'false'}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          is_active: e.target.value === 'true',
                        })
                      }
                      className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    >
                      <option value="true">启用</option>
                      <option value="false">禁用</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingCategory(null);
                }}
                className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 text-gray-700 hover:bg-gray-50 transition-colors font-medium"
              >
                取消
              </button>
              <button
                onClick={editingCategory ? handleUpdate : handleCreate}
                className="rounded-lg bg-blue-600 px-6 py-2.5 text-white hover:bg-blue-700 transition-colors font-medium shadow-sm"
              >
                {editingCategory ? '更新' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除分类类型确认对话框 */}
      {showDeleteTypeConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white shadow-2xl">
            <div className="bg-red-50 border-b border-red-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-red-900">确认删除分类类型</h3>
            </div>
            <div className="p-6">
              <p className="text-gray-700 mb-4">
                确定要删除分类类型{' '}
                <span className="font-semibold text-red-600">"{showDeleteTypeConfirm}"</span>{' '}
                及其下的所有{' '}
                <span className="font-semibold">
                  {categoriesByType[showDeleteTypeConfirm]?.length || 0}
                </span>{' '}
                个分类项吗？
              </p>
              <p className="text-sm text-red-600 mb-4">
                ⚠️ 此操作不可恢复！如果该类型下的分类项已被项目使用，删除可能会失败。
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteTypeConfirm(null)}
                  className="rounded-lg border border-gray-300 bg-white px-6 py-2.5 text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                >
                  取消
                </button>
                <button
                  onClick={() => handleDeleteType(showDeleteTypeConfirm)}
                  className="rounded-lg bg-red-600 px-6 py-2.5 text-white hover:bg-red-700 transition-colors font-medium"
                >
                  确认删除
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
