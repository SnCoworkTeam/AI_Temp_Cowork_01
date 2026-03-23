'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { GanttChart, Plus, Calendar, CheckCircle, Clock, Eye, X } from 'lucide-react';
import Link from 'next/link';
import TemplateSelector from './ProjectPlans/TemplateSelector';

interface ProjectPlan {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  version: string;
  is_active: boolean;
  is_baseline: boolean;
  start_date?: string;
  end_date?: string;
  task_count: number;
  created_at: string;
  updated_at: string;
}

interface ProjectPlansSectionProps {
  projectId: string;
}

export default function ProjectPlansSection({ projectId }: ProjectPlansSectionProps) {
  const router = useRouter();
  const [plans, setPlans] = useState<ProjectPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    template_id: null as string | null,
  });
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);

  const fetchPlans = useCallback(async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans?limit=100`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data.items || []);
      } else {
        setError('获取项目计划列表失败');
      }
    } catch (error) {
      console.error('获取项目计划列表失败:', error);
      setError('获取项目计划列表失败');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      fetchPlans();
    }
  }, [projectId, fetchPlans]);

  const handleCreatePlan = async () => {
    try {
      setCreating(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description || undefined,
          start_date: formData.start_date || undefined,
          end_date: formData.end_date || undefined,
          template_id: formData.template_id || undefined,
        }),
      });

      if (response.ok) {
        const newPlan = await response.json();
        setPlans([newPlan, ...plans]);
        setShowCreateModal(false);
        setFormData({ name: '', description: '', start_date: '', end_date: '', template_id: null });
        setShowTemplateSelector(false);
        // 跳转到计划详情页面
        router.push(`/projects/plans/${newPlan.id}?projectId=${projectId}`);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || '创建计划失败');
      }
    } catch (error) {
      console.error('创建计划失败:', error);
      alert('创建计划失败');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <GanttChart className="w-5 h-5 text-indigo-600" />
            项目计划
          </h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>创建计划</span>
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 mb-4">
            {error}
          </div>
        )}

        {plans.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <GanttChart className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-600 mb-2">暂无项目计划</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-indigo-600 hover:text-indigo-700 font-medium"
            >
              创建第一个计划
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-gray-900 mb-1">{plan.name}</h3>
                    {plan.description && (
                      <p className="text-sm text-gray-600 line-clamp-2">{plan.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {plan.is_active && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                        活跃
                      </span>
                    )}
                    {plan.is_baseline && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                        基线
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>版本: {plan.version}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <CheckCircle className="w-4 h-4" />
                    <span>任务数: {plan.task_count}</span>
                  </div>
                  {plan.start_date && plan.end_date && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>
                        {new Date(plan.start_date).toLocaleDateString()} -{' '}
                        {new Date(plan.end_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 pt-3 border-t border-gray-200">
                  <Link
                    href={`/projects/plans/${plan.id}?projectId=${projectId}`}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors text-sm font-medium"
                  >
                    <Eye className="w-4 h-4" />
                    <span>查看详情</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 创建计划模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">创建项目计划</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    选择模板（可选）
                  </label>
                  <div className="mb-4">
                    <button
                      type="button"
                      onClick={() => setShowTemplateSelector(!showTemplateSelector)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-left flex items-center justify-between"
                    >
                      <span className="text-gray-700">
                        {formData.template_id
                          ? `已选择模板 (ID: ${formData.template_id.substring(0, 8)}...)`
                          : '点击选择模板（可选）'}
                      </span>
                      <span className="text-gray-400">
                        {showTemplateSelector ? '收起' : '展开'}
                      </span>
                    </button>
                    {showTemplateSelector && (
                      <div className="mt-2 border border-gray-200 rounded-lg p-4 bg-gray-50 max-h-96 overflow-y-auto">
                        <TemplateSelector
                          onSelect={(templateId) => {
                            setFormData({ ...formData, template_id: templateId });
                            setShowTemplateSelector(false);
                          }}
                          selectedTemplateId={formData.template_id}
                        />
                      </div>
                    )}
                    {formData.template_id && (
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, template_id: null })}
                        className="mt-2 text-sm text-red-600 hover:text-red-700"
                      >
                        清除模板选择
                      </button>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    计划名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    placeholder="请输入计划名称"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">计划描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    placeholder="请输入计划描述（可选）"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">开始日期</label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">结束日期</label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                    />
                  </div>
                </div>
              </div>
            </div>
            <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreatePlan}
                disabled={!formData.name || creating}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
