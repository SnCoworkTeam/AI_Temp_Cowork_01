'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, Calendar, TrendingUp, FileText, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface ProjectPlan {
  id: string;
  name: string;
  description?: string;
  version: string;
  is_active: boolean;
  is_baseline: boolean;
  start_date?: string;
  end_date?: string;
  task_count: number;
  project_id: string;
  project_name?: string;
}

export default function ProjectPlansPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<ProjectPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);

  useEffect(() => {
    // 从URL参数获取project_id
    if (typeof window !== 'undefined') {
      try {
        const params = new URLSearchParams(window.location.search);
        const pid = params.get('project_id');
        if (pid) {
          setProjectId(pid);
          fetchPlans(pid);
        } else {
          setError('缺少项目ID参数，请从项目详情页进入');
          setLoading(false);
        }
      } catch (err) {
        console.error('获取项目ID失败:', err);
        setError('获取项目ID失败');
        setLoading(false);
      }
    } else {
      // 服务器端渲染时，设置加载状态
      setLoading(false);
    }
  }, []);

  const fetchPlans = async (pid: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${pid}/plans`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data.items || []);
      } else {
        setError('加载计划列表失败');
      }
    } catch (error) {
      console.error('获取计划列表失败:', error);
      setError('加载计划列表失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
          <p className="font-semibold mb-2">{error}</p>
          <div className="flex gap-4 mt-4">
            <Link href="/projects" className="text-blue-600 hover:underline">
              返回项目列表
            </Link>
            {projectId && (
              <Link href={`/projects/${projectId}`} className="text-blue-600 hover:underline">
                返回项目详情
              </Link>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>返回</span>
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">项目计划管理</h1>
            <p className="text-gray-600 mt-1">管理和查看项目计划</p>
          </div>
        </div>
        {projectId && (
          <Link
            href={`/projects/${projectId}/plans/create`}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>创建计划</span>
          </Link>
        )}
      </div>

      {/* 计划列表 */}
      {plans.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-12 text-center">
          <Calendar className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500 text-lg mb-4">暂无项目计划</p>
          {projectId && (
            <Link
              href={`/projects/${projectId}/plans/create`}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span>创建第一个计划</span>
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <Link
              key={plan.id}
              href={`/projects/${plan.project_id}/plans/${plan.id}`}
              className="bg-white rounded-xl shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{plan.name}</h3>
                  {plan.description && (
                    <p className="text-sm text-gray-600 line-clamp-2">{plan.description}</p>
                  )}
                </div>
                {plan.is_baseline && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    基线
                  </span>
                )}
              </div>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  <span>版本: {plan.version}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span>任务数: {plan.task_count}</span>
                </div>
                {plan.start_date && plan.end_date && (
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    <span>
                      {new Date(plan.start_date).toLocaleDateString()} -{' '}
                      {new Date(plan.end_date).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <span
                  className={`text-sm font-medium ${plan.is_active ? 'text-green-600' : 'text-gray-400'}`}
                >
                  {plan.is_active ? '激活' : '未激活'}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
