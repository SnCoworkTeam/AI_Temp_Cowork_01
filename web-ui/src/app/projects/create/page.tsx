'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Save, X, Building2, Calendar, Users, DollarSign, TrendingUp, CheckCircle, FileText, Target } from 'lucide-react';
import { getUsers, User } from '@/lib/api/admin';
import ErrorMessage from '@/components/ErrorMessage';

export default function CreateProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'planning',
    priority: 'medium',
    manager_id: '',
    reporter_id: '',
    start_date: '',
    end_date: '',
    budget: '',
    progress_percent: '',
    health_score: '',
    requires_weekly_report: false,
    milestone_implementation_start: '',
    milestone_solution_confirmation: '',
    milestone_delivery_online: '',
    milestone_project_acceptance: '',
    basic_data_categories: {} as Record<string, string>,
  });
  const [categories, setCategories] = useState<any[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);

  // 加载用户列表
  useEffect(() => {
    const loadUsers = async () => {
      try {
        const response = await getUsers({ page: 1, page_size: 100 });
        const usersList = (response as any).users || (response as any).items || [];
        setUsers(usersList);
      } catch (error) {
        console.error('加载用户列表失败:', error);
      }
    };
    loadUsers();
  }, []);

  // 加载基础数据分类
  useEffect(() => {
    const loadCategories = async () => {
      try {
        setLoadingCategories(true);
        const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
        const token = getAccessToken();

        const response = await fetch(`${apiUrl}/api/v1/basic-data/categories?limit=1000`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setCategories(data.items || []);
        }
      } catch (error) {
        console.error('加载基础数据分类失败:', error);
      } finally {
        setLoadingCategories(false);
      }
    };

    loadCategories();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          budget: formData.budget ? parseFloat(formData.budget) : null,
          progress_percent: formData.progress_percent
            ? parseFloat(formData.progress_percent)
            : null,
          health_score: formData.health_score ? parseFloat(formData.health_score) : null,
          manager_id: formData.manager_id || null,
          reporter_id: formData.reporter_id || null,
          basic_data_category_ids: Object.values(formData.basic_data_categories).filter(
            (id) => id
          ) as string[],
        }),
      });

      if (response.ok) {
        router.push('/projects');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '创建项目失败');
      }
    } catch (error: any) {
      console.error('创建项目失败:', error);
      setError(error?.message || '创建项目失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理基础数据分类
  const processedCategories = (() => {
    const allowedTypes = ['project_phase', 'phase_status', 'application_domain', 'project_category'];
    const grouped = categories
      .filter((cat: any) => allowedTypes.includes(cat.category_type))
      .reduce((acc: any, cat: any) => {
        if (!acc[cat.category_type]) {
          acc[cat.category_type] = [];
        }
        acc[cat.category_type].push(cat);
        return acc;
      }, {});

    const processed: Record<string, any[]> = {};
    Object.entries(grouped).forEach(([type, items]: [string, any]) => {
      if (type === 'application_domain') {
        const allowedCodes = ['01-', '02-', '03-', '04-', '05-', '06-', '07-', '08-', '09-', '10-', '11-', '12-', '99-'];
        const filteredItems = (items as any[]).filter((item) => {
          if (!item.code) return false;
          return allowedCodes.some((code) => item.code.startsWith(code));
        });
        processed[type] = filteredItems.sort((a, b) => {
          const aCode = a.code || '';
          const bCode = b.code || '';
          return aCode.localeCompare(bCode);
        });
      } else {
        const sortedItems = (items as any[]).sort((a, b) => {
          const aHasCode = a.code && /^\d{2}-/.test(a.code);
          const bHasCode = b.code && /^\d{2}-/.test(b.code);
          if (aHasCode && !bHasCode) return -1;
          if (!aHasCode && bHasCode) return 1;
          return 0;
        });
        processed[type] = sortedItems;
      }
    });

    const categoryTypeNames: Record<string, string> = {
      project_phase: '项目阶段',
      phase_status: '阶段状态',
      application_domain: '应用领域',
      project_category: '项目分类',
    };

    const categoryOrder: Record<string, number> = {
      project_phase: 1,
      phase_status: 2,
      application_domain: 3,
      project_category: 4,
    };

    return Object.entries(processed)
      .sort(([typeA], [typeB]) => {
        const orderA = categoryOrder[typeA] ?? 999;
        const orderB = categoryOrder[typeB] ?? 999;
        return orderA - orderB;
      })
      .map(([type, items]) => ({
        type,
        name: categoryTypeNames[type] || type,
        items,
      }));
  })();

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 页面头部 */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl shadow-xl border-2 border-blue-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500 rounded-xl shadow-lg">
              <Building2 className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">新建项目</h1>
              <p className="text-sm text-gray-600 mt-1">创建新的项目，填写项目基本信息</p>
            </div>
          </div>
          <button
            onClick={() => router.back()}
            className="px-5 py-2.5 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 flex items-center gap-2 font-semibold shadow-md hover:shadow-lg"
          >
            <X className="h-5 w-5" />
            取消
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 段落1: 基本信息 */}
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-5 border-b-2 border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500 rounded-lg">
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">基本信息</h2>
            </div>
          </div>
          <div className="p-6 space-y-6">
            {/* 提示信息 */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-blue-900 mb-1">💡 提示</p>
                  <p className="text-sm text-blue-800 leading-relaxed">
                    项目编码将自动生成，格式为{' '}
                    <span className="font-mono font-semibold">ZHGJ-年-4位数字编号</span>
                    （例如：ZHGJ-2025-0001）
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 项目名称 */}
              <div className="md:col-span-2">
                <label className="block text-sm font-bold text-gray-700 mb-2">
                  项目名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                  placeholder="请输入项目名称"
                />
              </div>

              {/* 项目描述 */}
              <div className="md:col-span-2">
                <label className="block text-sm font-bold text-gray-700 mb-2">项目描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 resize-none bg-white"
                  placeholder="请输入项目描述..."
                />
              </div>

              {/* 项目状态 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">项目状态</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                >
                  <option value="planning">规划中</option>
                  <option value="active">进行中</option>
                  <option value="delayed">已延迟</option>
                  <option value="completed">已完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </div>

              {/* 优先级 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">优先级</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                >
                  <option value="low">低</option>
                  <option value="medium">中</option>
                  <option value="high">高</option>
                  <option value="critical">紧急</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* 段落2: 时间信息 */}
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 px-6 py-5 border-b-2 border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500 rounded-lg">
                <Calendar className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">时间信息</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 计划开始日期 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">计划开始日期</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 bg-white"
                />
              </div>

              {/* 计划结束日期 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">计划结束日期</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 bg-white"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 段落3: 人员信息 */}
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 px-6 py-5 border-b-2 border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500 rounded-lg">
                <Users className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">人员信息</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 项目经理 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">项目经理</label>
                <select
                  value={formData.manager_id}
                  onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-white"
                >
                  <option value="">请选择</option>
                  {users.map((user) => (
                    <option key={user.user_id} value={user.user_id}>
                      {user.display_name || user.username}
                    </option>
                  ))}
                </select>
              </div>

              {/* 填报人 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">填报人</label>
                <select
                  value={formData.reporter_id}
                  onChange={(e) => setFormData({ ...formData, reporter_id: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-white"
                >
                  <option value="">请选择</option>
                  {users.map((user) => (
                    <option key={user.user_id} value={user.user_id}>
                      {user.display_name || user.username}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* 段落4: 预算与进度 */}
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 px-6 py-5 border-b-2 border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500 rounded-lg">
                <DollarSign className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">预算与进度</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 预算 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">预算</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.budget}
                  onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white"
                  placeholder="0.00"
                />
              </div>

              {/* 进度 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">进度 (%)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={formData.progress_percent}
                  onChange={(e) => setFormData({ ...formData, progress_percent: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white"
                  placeholder="0.0"
                />
              </div>

              {/* 健康度 */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">健康度</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={formData.health_score}
                  onChange={(e) => setFormData({ ...formData, health_score: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white"
                  placeholder="0.0"
                />
              </div>
            </div>

            {/* 是否编写周报 */}
            <div className="mt-6">
              <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border-2 border-gray-200">
                <input
                  type="checkbox"
                  checked={formData.requires_weekly_report}
                  onChange={(e) =>
                    setFormData({ ...formData, requires_weekly_report: e.target.checked })
                  }
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                />
                <FileText className="w-5 h-5 text-gray-600" />
                <label className="text-sm font-semibold text-gray-700 cursor-pointer">
                  是否编写周报
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* 段落5: 项目分类 */}
        {!loadingCategories && processedCategories.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-50 via-blue-50 to-cyan-50 px-6 py-5 border-b-2 border-gray-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-500 rounded-lg">
                  <Target className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">项目分类</h2>
              </div>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {processedCategories.map(({ type, name, items }) => (
                  <div key={type}>
                    <label className="block text-sm font-bold text-gray-700 mb-2">{name}</label>
                    <select
                      value={formData.basic_data_categories[type] || ''}
                      onChange={(e) => {
                        setFormData({
                          ...formData,
                          basic_data_categories: {
                            ...formData.basic_data_categories,
                            [type]: e.target.value || '',
                          },
                        });
                      }}
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200 bg-white"
                    >
                      <option value="">请选择</option>
                      {items.map((cat: any) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 段落6: 重要里程碑 */}
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-yellow-50 via-amber-50 to-orange-50 px-6 py-5 border-b-2 border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500 rounded-lg">
                <CheckCircle className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">重要里程碑</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">实施启动</label>
                <input
                  type="date"
                  value={formData.milestone_implementation_start}
                  onChange={(e) =>
                    setFormData({ ...formData, milestone_implementation_start: e.target.value })
                  }
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">方案确认</label>
                <input
                  type="date"
                  value={formData.milestone_solution_confirmation}
                  onChange={(e) =>
                    setFormData({ ...formData, milestone_solution_confirmation: e.target.value })
                  }
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">交付上线</label>
                <input
                  type="date"
                  value={formData.milestone_delivery_online}
                  onChange={(e) =>
                    setFormData({ ...formData, milestone_delivery_online: e.target.value })
                  }
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">项目验收</label>
                <input
                  type="date"
                  value={formData.milestone_project_acceptance}
                  onChange={(e) =>
                    setFormData({ ...formData, milestone_project_acceptance: e.target.value })
                  }
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 表单底部操作栏 */}
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-2xl shadow-lg border-2 border-gray-200 px-6 py-5 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-8 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-semibold shadow-md hover:shadow-lg"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold shadow-lg hover:shadow-xl"
          >
            <Save className="h-5 w-5" />
            {loading ? '创建中...' : '创建项目'}
          </button>
        </div>
      </form>
    </div>
  );
}
