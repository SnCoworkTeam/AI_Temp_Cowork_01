'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getAccessToken } from '@/lib/auth';

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
  const router = useRouter();
  const [categories, setCategories] = useState<BasicDataCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<BasicDataCategory | null>(null);
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
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) {
        router.push('/login');
        return;
      }

      let url = `${apiUrl}/api/v1/basic-data/categories`;
      const params = new URLSearchParams();
      if (filterType) {
        params.append('category_type', filterType);
      }
      if (params.toString()) {
        url += '?' + params.toString();
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login');
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
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
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) {
        router.push('/login');
        return;
      }

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

      const response = await fetch(`${apiUrl}/api/v1/basic-data/categories`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '创建失败');
      }

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
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) {
        router.push('/login');
        return;
      }

      const payload: any = {
        code: formData.code,
        name: formData.name,
        description: formData.description || undefined,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
      };

      if (formData.parent_id) {
        payload.parent_id = formData.parent_id;
      }

      const response = await fetch(`${apiUrl}/api/v1/basic-data/categories/${editingCategory.id}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '更新失败');
      }

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
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(`${apiUrl}/api/v1/basic-data/categories/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '删除失败');
      }

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

  // 获取分类类型列表
  const categoryTypes = Array.from(new Set(categories.map((c) => c.category_type)));

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
              <h2 className="mb-4 text-xl font-semibold text-gray-900">{type}</h2>
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
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleEdit(category)}
                              className="text-blue-600 hover:text-blue-800"
                            >
                              编辑
                            </button>
                            <button
                              onClick={() => handleDelete(category.id)}
                              className="text-red-600 hover:text-red-800"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-xl font-semibold">
              {editingCategory ? '编辑分类' : '新建分类'}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">分类类型 *</label>
                <input
                  type="text"
                  value={formData.category_type}
                  onChange={(e) => setFormData({ ...formData, category_type: e.target.value })}
                  disabled={!!editingCategory}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
                  placeholder="如：project_type, industry, domain"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">编码 *</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
                  placeholder="分类编码"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">名称 *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
                  placeholder="分类名称"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
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
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
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
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
                  >
                    <option value="true">启用</option>
                    <option value="false">禁用</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-4">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingCategory(null);
                }}
                className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={editingCategory ? handleUpdate : handleCreate}
                className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
              >
                {editingCategory ? '更新' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
