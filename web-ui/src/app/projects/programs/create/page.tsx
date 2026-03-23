'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { getUsers, User } from '@/lib/api/admin';
import {
  ArrowLeft,
  Building2,
  Calendar,
  Users,
  DollarSign,
  Save,
  X,
  AlertCircle,
} from 'lucide-react';
import ErrorMessage from '@/components/ErrorMessage';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface BasicDataCategory {
  id: string;
  name: string;
  code: string;
  category_type: string;
}

export default function CreateProgramPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [categories, setCategories] = useState<BasicDataCategory[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'planning',
    manager_id: '',
    start_date: '',
    end_date: '',
    budget: '',
    category_id: '',
  });

  useEffect(() => {
    loadUsers();
    loadCategories();
  }, []);

  const loadUsers = async () => {
    try {
      // 使用更小的 page_size，避免 422 错误
      const response = await getUsers({ page: 1, page_size: 100 });
      // 处理不同的响应格式
      const usersList = (response as any).users || (response as any).items || response || [];
      setUsers(Array.isArray(usersList) ? usersList : []);
    } catch (error: any) {
      console.error('加载用户列表失败:', error);
      // 不阻止页面渲染，只记录错误
      setUsers([]);
    }
  };

  const loadCategories = async () => {
    try {
      setLoadingCategories(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/basic-data/categories?category_type=project_category&limit=1000`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCategories(data.items || []);
      }
    } catch (error) {
      console.error('加载分类列表失败:', error);
    } finally {
      setLoadingCategories(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setError('项目群名称不能为空');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const submitData: any = {
        name: formData.name,
        description: formData.description || null,
        status: formData.status,
        manager_id: formData.manager_id || null,
        start_date: formData.start_date || null,
        end_date: formData.end_date || null,
        budget: formData.budget ? parseFloat(formData.budget) : null,
        category_id: formData.category_id || null,
      };

      const response = await fetch(`${apiUrl}/api/v1/programs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(submitData),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/projects/programs/${data.id}`);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '创建项目群失败' }));
        setError(errorData.detail || '创建项目群失败');
      }
    } catch (error: any) {
      console.error('创建项目群失败:', error);
      setError(error?.message || '创建项目群失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 错误提示 */}
        {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}

        {/* 头部 */}
        <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-lg border-2 border-indigo-200 p-6 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-white/80 rounded-lg transition-all shadow-sm hover:shadow-md"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>返回</span>
            </button>
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-500 rounded-xl shadow-lg">
                <Building2 className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">创建项目群</h1>
                <p className="text-gray-600 mt-1">创建新的项目群，设置基本信息和管理配置</p>
              </div>
            </div>
          </div>
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 px-8 py-5 border-b-2 border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">基本信息</h2>
          </div>

          <div className="p-8 space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                项目群名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                placeholder="请输入项目群名称"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">描述</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                placeholder="请输入项目群描述"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">状态</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                >
                  <option value="planning">规划中</option>
                  <option value="active">进行中</option>
                  <option value="delayed">已延迟</option>
                  <option value="completed">已完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">项目经理</label>
                <select
                  value={formData.manager_id}
                  onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                >
                  <option value="">请选择</option>
                  {users.map((user) => (
                    <option key={user.user_id} value={user.user_id}>
                      {user.display_name || user.full_name || user.username || user.email}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">开始日期</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">结束日期</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">预算</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <DollarSign className="w-5 h-5 text-gray-400" />
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                    className="w-full pl-12 pr-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">分类</label>
                <select
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                >
                  <option value="">请选择</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name} ({category.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* 底部操作按钮 */}
          <div className="bg-gray-50 px-8 py-6 border-t-2 border-gray-200 flex items-center justify-end gap-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-3 text-gray-700 bg-white border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-all font-semibold"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>创建中...</span>
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  <span>创建项目群</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </ErrorBoundary>
  );
}

