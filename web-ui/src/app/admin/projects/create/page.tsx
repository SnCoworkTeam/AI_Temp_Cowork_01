'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Save, X } from 'lucide-react';
import { getUsers, User } from '@/lib/api/admin';

export default function CreateProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
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
    milestone_implementation_start: '', // 实施启动日期
    milestone_solution_confirmation: '', // 方案确认日期
    milestone_delivery_online: '', // 交付上线日期
    milestone_project_acceptance: '', // 项目验收日期
    basic_data_categories: {} as Record<string, string>, // 改为对象，每个分类类型对应一个分类ID
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
        router.push('/admin/projects');
      } else {
        const error = await response.json();
        alert(error.detail || '创建项目失败');
      }
    } catch (error) {
      console.error('创建项目失败:', error);
      alert('创建项目失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">新建项目</h1>
          <p className="text-sm text-gray-600 mt-1">创建新的项目，填写项目基本信息</p>
        </div>
        <button
          onClick={() => router.back()}
          className="px-4 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 flex items-center gap-2 font-medium shadow-sm"
        >
          <X className="h-4 w-4" />
          取消
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
      >
        {/* 表单头部 */}
        <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-5 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <div className="w-1 h-5 bg-blue-600 rounded-full"></div>
            基本信息
          </h2>
        </div>

        <div className="p-6 space-y-6">
          {/* 提示信息 */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-2">
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                项目名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                placeholder="请输入项目名称"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">项目描述</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 resize-none bg-white"
                placeholder="请输入项目描述..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">项目状态</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
              >
                <option value="planning">规划中</option>
                <option value="active">进行中</option>
                <option value="delayed">已延迟</option>
                <option value="completed">已完成</option>
                <option value="cancelled">已取消</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">优先级</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
              >
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
                <option value="critical">紧急</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">计划开始日期</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">计划结束日期</label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">项目经理</label>
              <select
                value={formData.manager_id}
                onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
              >
                <option value="">请选择</option>
                {users.map((user) => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.display_name || user.username}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">填报人</label>
              <select
                value={formData.reporter_id}
                onChange={(e) => setFormData({ ...formData, reporter_id: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
              >
                <option value="">请选择</option>
                {users.map((user) => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.display_name || user.username}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">预算</label>
              <input
                type="number"
                step="0.01"
                value={formData.budget}
                onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">进度 (%)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formData.progress_percent}
                onChange={(e) => setFormData({ ...formData, progress_percent: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                placeholder="0.0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">健康度</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formData.health_score}
                onChange={(e) => setFormData({ ...formData, health_score: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                placeholder="0.0"
              />
            </div>

            <div className="md:col-span-2">
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <input
                  type="checkbox"
                  checked={formData.requires_weekly_report}
                  onChange={(e) =>
                    setFormData({ ...formData, requires_weekly_report: e.target.checked })
                  }
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                />
                <label className="text-sm font-medium text-gray-700 cursor-pointer">
                  是否编写周报
                </label>
              </div>
            </div>

            {/* 基础数据分类选择 - 下拉框单选 */}
            {!loadingCategories && categories.length > 0 && (
              <>
                {Object.entries(
                  categories
                    .filter((cat: any) => cat.category_type !== 'project_status') // 过滤掉 project_status
                    .reduce((acc: any, cat: any) => {
                      if (!acc[cat.category_type]) {
                        acc[cat.category_type] = [];
                      }
                      acc[cat.category_type].push(cat);
                      return acc;
                    }, {})
                ).map(([type, items]: [string, any]) => {
                  const categoryTypeNames: Record<string, string> = {
                    industry_chain: '产业链',
                    production_base: '生产基地/业务单元',
                    project_phase: '项目阶段',
                    phase_status: '阶段状态',
                    application_domain: '应用领域',
                    project_category: '项目分类',
                  };

                  return (
                    <div key={type}>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {categoryTypeNames[type] || type}
                      </label>
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
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                      >
                        <option value="">请选择</option>
                        {items.map((cat: any) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </>
            )}

            {/* 重要里程碑日期 */}
            <div className="md:col-span-2 border-t border-gray-200 pt-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">重要里程碑</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">实施启动</label>
                  <input
                    type="date"
                    value={formData.milestone_implementation_start}
                    onChange={(e) =>
                      setFormData({ ...formData, milestone_implementation_start: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">方案确认</label>
                  <input
                    type="date"
                    value={formData.milestone_solution_confirmation}
                    onChange={(e) =>
                      setFormData({ ...formData, milestone_solution_confirmation: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">交付上线</label>
                  <input
                    type="date"
                    value={formData.milestone_delivery_online}
                    onChange={(e) =>
                      setFormData({ ...formData, milestone_delivery_online: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">项目验收</label>
                  <input
                    type="date"
                    value={formData.milestone_project_acceptance}
                    onChange={(e) =>
                      setFormData({ ...formData, milestone_project_acceptance: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 表单底部操作栏 */}
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-5 border-t border-gray-200 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-md hover:shadow-lg"
          >
            <Save className="h-4 w-4" />
            {loading ? '创建中...' : '创建项目'}
          </button>
        </div>
      </form>
    </div>
  );
}
