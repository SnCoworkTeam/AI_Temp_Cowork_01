'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import {
  ArrowLeft,
  Building2,
  Calendar,
  Users,
  TrendingUp,
  DollarSign,
  Target,
  Edit,
  Trash2,
  Plus,
  FileText,
  Heart,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import Link from 'next/link';
import ErrorMessage from '@/components/ErrorMessage';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface Program {
  id: string;
  program_code: string;
  name: string;
  description?: string;
  status: string;
  manager_id?: string;
  manager_name?: string;
  start_date?: string;
  end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  budget?: number;
  actual_cost?: number;
  progress_percent: number;
  health_score: number;
  category_id?: string;
  category_name?: string;
  project_count: number;
  created_at: string;
  updated_at: string;
}

interface Project {
  id: string;
  project_code: string;
  name: string;
  status: string;
  progress_percent: number;
  manager_name?: string;
  start_date?: string;
  end_date?: string;
}

export default function ProgramDetailPage() {
  const params = useParams();
  const router = useRouter();
  const programId = params?.id as string;

  const [program, setProgram] = useState<Program | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (programId) {
      fetchProgram();
      fetchProjects();
    }
  }, [programId]);

  const fetchProgram = async () => {
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/programs/${programId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProgram(data);
      } else if (response.status === 404) {
        setError('项目群不存在');
      } else {
        const errorData = await response.json().catch(() => ({ detail: '加载项目群失败' }));
        setError(errorData.detail || '加载项目群失败');
      }
    } catch (error: any) {
      console.error('获取项目群详情失败:', error);
      setError(error?.message || '加载项目群失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoadingProjects(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects?program_id=${programId}&limit=100`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data.items || []);
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
    } finally {
      setLoadingProjects(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'planning':
        return 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 border-gray-300';
      case 'active':
        return 'bg-gradient-to-r from-green-100 to-emerald-200 text-green-700 border-green-300';
      case 'delayed':
        return 'bg-gradient-to-r from-yellow-100 to-amber-200 text-yellow-700 border-yellow-300';
      case 'completed':
        return 'bg-gradient-to-r from-blue-100 to-cyan-200 text-blue-700 border-blue-300';
      case 'cancelled':
        return 'bg-gradient-to-r from-red-100 to-rose-200 text-red-700 border-red-300';
      default:
        return 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 border-gray-300';
    }
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      planning: '规划中',
      active: '进行中',
      delayed: '已延迟',
      completed: '已完成',
      cancelled: '已取消',
    };
    return statusMap[status?.toLowerCase()] || status;
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'from-green-500 to-emerald-600';
    if (score >= 60) return 'from-yellow-500 to-amber-600';
    return 'from-red-500 to-rose-600';
  };

  const getHealthTextColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error || !program) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <ErrorMessage message={error || '项目群不存在'} type="error" />
        <div className="mt-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>返回</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="max-w-7xl mx-auto space-y-6 p-6">
        {/* 错误提示 */}
        <ErrorMessage message={error} type="error" onClose={() => setError(null)} />

        {/* 头部 - 优化设计 */}
        <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl shadow-xl overflow-hidden">
          <div className="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div className="relative bg-white/10 backdrop-blur-md p-5 lg:p-6">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
              <div className="flex items-start gap-4 flex-1 min-w-0 w-full lg:w-auto">
                <button
                  onClick={() => router.back()}
                  className="flex items-center gap-2 px-3 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-all duration-200 backdrop-blur-sm shadow-md hover:shadow-lg transform hover:scale-105 flex-shrink-0"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span className="font-medium text-sm">返回</span>
                </button>
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm shadow-lg flex-shrink-0">
                    <Building2 className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h1 className="text-2xl lg:text-3xl font-bold text-white mb-1.5 break-words leading-tight">
                      {program.name}
                    </h1>
                    <p className="text-white/90 font-mono text-sm mb-2">{program.program_code}</p>
                    {program.description && (
                      <p className="text-white/80 text-sm mt-2 max-w-2xl leading-relaxed line-clamp-2">
                        {program.description}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0 w-full lg:w-auto justify-start lg:justify-end">
                <span
                  className={`px-4 py-1.5 rounded-full text-xs font-semibold border backdrop-blur-sm shadow-md ${
                    program.status === 'active'
                      ? 'bg-green-500/30 text-white border-green-300/50'
                      : program.status === 'completed'
                        ? 'bg-blue-500/30 text-white border-blue-300/50'
                        : program.status === 'delayed'
                          ? 'bg-yellow-500/30 text-white border-yellow-300/50'
                          : 'bg-white/20 text-white border-white/30'
                  }`}
                >
                  {getStatusText(program.status)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 统计卡片 - 优化比例 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-gradient-to-br from-blue-50 via-blue-100 to-indigo-100 rounded-2xl shadow-xl border-2 border-blue-200 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <div className="flex-1">
                <p className="text-sm font-semibold text-blue-600 mb-2 uppercase tracking-wide">项目数量</p>
                <p className="text-4xl font-bold text-blue-900">{program.project_count}</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-lg">
                <Building2 className="w-7 h-7 text-white" />
              </div>
            </div>
            <div className="pt-3 border-t border-blue-200">
              <p className="text-xs text-blue-600 font-medium">包含项目总数</p>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 via-emerald-100 to-teal-100 rounded-2xl shadow-xl border-2 border-green-200 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <div className="flex-1">
                <p className="text-sm font-semibold text-green-600 mb-2 uppercase tracking-wide">整体进度</p>
                <p className="text-4xl font-bold text-green-900">{program.progress_percent.toFixed(1)}%</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-lg">
                <TrendingUp className="w-7 h-7 text-white" />
              </div>
            </div>
            <div className="pt-3 border-t border-green-200">
              <div className="w-full bg-green-200 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-green-500 to-emerald-600 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${program.progress_percent}%` }}
                />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 via-purple-100 to-pink-100 rounded-2xl shadow-xl border-2 border-purple-200 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <div className="flex-1">
                <p className="text-sm font-semibold text-purple-600 mb-2 uppercase tracking-wide">健康度</p>
                <p className={`text-4xl font-bold ${getHealthTextColor(program.health_score)}`}>
                  {program.health_score.toFixed(1)}%
                </p>
              </div>
              <div className={`p-4 bg-gradient-to-br ${getHealthColor(program.health_score)} rounded-2xl shadow-lg`}>
                <Heart className="w-7 h-7 text-white" />
              </div>
            </div>
            <div className="pt-3 border-t border-purple-200">
              <div className="w-full bg-purple-200 rounded-full h-2">
                <div
                  className={`bg-gradient-to-r ${getHealthColor(program.health_score)} h-2 rounded-full transition-all duration-1000`}
                  style={{ width: `${program.health_score}%` }}
                />
              </div>
            </div>
          </div>

          {program.budget !== undefined && program.budget !== null ? (
            <div className="bg-gradient-to-br from-amber-50 via-amber-100 to-yellow-100 rounded-2xl shadow-xl border-2 border-amber-200 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="flex items-center justify-between mb-4">
                <div className="flex-1">
                  <p className="text-sm font-semibold text-amber-600 mb-2 uppercase tracking-wide">预算</p>
                  <p className="text-3xl font-bold text-amber-900">
                    ¥{(program.budget / 10000).toFixed(1)}万
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-br from-amber-500 to-yellow-600 rounded-2xl shadow-lg">
                  <DollarSign className="w-7 h-7 text-white" />
                </div>
              </div>
              {program.actual_cost !== undefined && program.actual_cost !== null && (
                <div className="pt-3 border-t border-amber-200">
                  <p className="text-xs text-amber-600 font-medium">
                    已使用: {((program.actual_cost / program.budget) * 100).toFixed(1)}%
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gradient-to-br from-gray-50 via-gray-100 to-slate-100 rounded-2xl shadow-xl border-2 border-gray-200 p-6 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="flex items-center justify-between mb-4">
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-600 mb-2 uppercase tracking-wide">创建时间</p>
                  <p className="text-lg font-bold text-gray-900">
                    {new Date(program.created_at).toLocaleDateString('zh-CN')}
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-br from-gray-500 to-slate-600 rounded-2xl shadow-lg">
                  <Clock className="w-7 h-7 text-white" />
                </div>
              </div>
              <div className="pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-600 font-medium">项目群创建日期</p>
              </div>
            </div>
          )}
        </div>

        {/* 基本信息卡片 - 优化布局 */}
        <div className="bg-white rounded-3xl shadow-xl border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 px-8 py-5 border-b-2 border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              基本信息
            </h2>
          </div>
          <div className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {program.manager_name && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border-2 border-blue-100 hover:shadow-lg transition-all duration-300">
                  <label className="text-sm font-bold text-blue-700 flex items-center gap-2 mb-3 uppercase tracking-wide">
                    <div className="p-2 bg-blue-500 rounded-lg shadow-md">
                      <Users className="w-4 h-4 text-white" />
                    </div>
                    项目经理
                  </label>
                  <p className="text-gray-900 font-semibold text-lg">{program.manager_name}</p>
                </div>
              )}
              {program.category_name && (
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-5 border-2 border-purple-100 hover:shadow-lg transition-all duration-300">
                  <label className="text-sm font-bold text-purple-700 mb-3 uppercase tracking-wide">分类</label>
                  <p className="text-gray-900 font-semibold text-lg">{program.category_name}</p>
                </div>
              )}
              {program.start_date && program.end_date && (
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-5 border-2 border-green-100 hover:shadow-lg transition-all duration-300">
                  <label className="text-sm font-bold text-green-700 flex items-center gap-2 mb-3 uppercase tracking-wide">
                    <div className="p-2 bg-green-500 rounded-lg shadow-md">
                      <Calendar className="w-4 h-4 text-white" />
                    </div>
                    计划时间
                  </label>
                  <p className="text-gray-900 font-semibold text-base">
                    {new Date(program.start_date).toLocaleDateString('zh-CN')} -{' '}
                    {new Date(program.end_date).toLocaleDateString('zh-CN')}
                  </p>
                </div>
              )}
              {program.actual_start_date && program.actual_end_date && (
                <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-5 border-2 border-orange-100 hover:shadow-lg transition-all duration-300">
                  <label className="text-sm font-bold text-orange-700 flex items-center gap-2 mb-3 uppercase tracking-wide">
                    <div className="p-2 bg-orange-500 rounded-lg shadow-md">
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    </div>
                    实际时间
                  </label>
                  <p className="text-gray-900 font-semibold text-base">
                    {new Date(program.actual_start_date).toLocaleDateString('zh-CN')} -{' '}
                    {new Date(program.actual_end_date).toLocaleDateString('zh-CN')}
                  </p>
                </div>
              )}
              {program.budget !== undefined && program.budget !== null && (
                <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-xl p-5 border-2 border-amber-100 hover:shadow-lg transition-all duration-300">
                  <label className="text-sm font-bold text-amber-700 flex items-center gap-2 mb-3 uppercase tracking-wide">
                    <div className="p-2 bg-amber-500 rounded-lg shadow-md">
                      <DollarSign className="w-4 h-4 text-white" />
                    </div>
                    预算
                  </label>
                  <p className="text-gray-900 font-semibold text-xl">¥{program.budget.toLocaleString()}</p>
                </div>
              )}
              {program.actual_cost !== undefined && program.actual_cost !== null && (
                <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-xl p-5 border-2 border-red-100 hover:shadow-lg transition-all duration-300">
                  <label className="text-sm font-bold text-red-700 flex items-center gap-2 mb-3 uppercase tracking-wide">
                    <div className="p-2 bg-red-500 rounded-lg shadow-md">
                      <DollarSign className="w-4 h-4 text-white" />
                    </div>
                    实际成本
                  </label>
                  <p className="text-gray-900 font-semibold text-xl">¥{program.actual_cost.toLocaleString()}</p>
                  {program.budget && (
                    <div className="mt-3 pt-3 border-t border-red-200">
                      <p className="text-xs text-gray-600 font-medium">
                        预算使用率: <span className="font-bold text-red-600">{((program.actual_cost / program.budget) * 100).toFixed(1)}%</span>
                      </p>
                      <div className="w-full bg-red-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-gradient-to-r from-red-500 to-rose-600 h-2 rounded-full transition-all duration-1000"
                          style={{ width: `${Math.min((program.actual_cost / program.budget) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 进度和健康度 - 优化视觉平衡 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-3xl shadow-xl border-2 border-blue-200 p-8 hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="p-4 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-lg">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">整体进度</h3>
                  <p className="text-sm text-gray-600 mt-1">项目群整体完成情况</p>
                </div>
              </div>
              <span className="text-5xl font-bold text-blue-600">{program.progress_percent.toFixed(1)}%</span>
            </div>
            <div className="relative">
              <div className="w-full bg-blue-200 rounded-full h-5 shadow-inner">
                <div
                  className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 h-5 rounded-full transition-all duration-1000 shadow-lg"
                  style={{ width: `${program.progress_percent}%` }}
                />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 rounded-3xl shadow-xl border-2 border-green-200 p-8 hover:shadow-2xl transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className={`p-4 bg-gradient-to-br ${getHealthColor(program.health_score)} rounded-2xl shadow-lg`}>
                  <Target className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">健康度</h3>
                  <p className="text-sm text-gray-600 mt-1">项目群健康状态评估</p>
                </div>
              </div>
              <span className={`text-5xl font-bold ${getHealthTextColor(program.health_score)}`}>
                {program.health_score.toFixed(1)}%
              </span>
            </div>
            <div className="relative">
              <div className="w-full bg-green-200 rounded-full h-5 shadow-inner">
                <div
                  className={`bg-gradient-to-r ${getHealthColor(program.health_score)} h-5 rounded-full transition-all duration-1000 shadow-lg`}
                  style={{ width: `${program.health_score}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 项目列表 - 优化设计 */}
        <div className="bg-white rounded-3xl shadow-xl border-2 border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 px-8 py-6 border-b-2 border-gray-200">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                项目列表
                <span className="px-4 py-1.5 bg-white rounded-full text-sm font-bold text-indigo-600 border-2 border-indigo-200 shadow-md">
                  {projects.length}
                </span>
              </h2>
              <Link
                href={`/projects/create?program_id=${programId}`}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 font-semibold"
              >
                <Plus className="w-5 h-5" />
                <span>添加项目</span>
              </Link>
            </div>
          </div>
          <div className="p-8">
            {loadingProjects ? (
              <div className="flex items-center justify-center py-16">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-4"></div>
                  <p className="text-gray-600">加载项目中...</p>
                </div>
              </div>
            ) : projects.length === 0 ? (
              <div className="text-center py-16">
                <div className="p-4 bg-gray-100 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
                  <Building2 className="w-10 h-10 text-gray-400" />
                </div>
                <p className="text-gray-500 text-lg mb-2 font-semibold">暂无项目</p>
                <p className="text-gray-400 text-sm mb-6">开始创建第一个项目吧</p>
                <Link
                  href={`/projects/create?program_id=${programId}`}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 font-semibold"
                >
                  <Plus className="w-5 h-5" />
                  <span>创建第一个项目</span>
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {projects.map((project) => (
                  <Link
                    key={project.id}
                    href={`/projects/${project.id}`}
                    className="group block bg-gradient-to-br from-white via-gray-50 to-gray-100 rounded-2xl border-2 border-gray-200 hover:border-indigo-400 hover:shadow-2xl transition-all duration-300 overflow-hidden transform hover:scale-[1.02]"
                  >
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors line-clamp-2">
                            {project.name}
                          </h3>
                          <p className="text-sm text-gray-500 font-mono mb-3">{project.project_code}</p>
                        </div>
                        <span
                          className={`px-3 py-1.5 rounded-full text-xs font-bold border-2 flex-shrink-0 ${getStatusColor(project.status)}`}
                        >
                          {getStatusText(project.status)}
                        </span>
                      </div>

                      <div className="space-y-3 mb-4">
                        {project.manager_name && (
                          <div className="flex items-center gap-2 text-sm text-gray-700">
                            <div className="p-1.5 bg-blue-100 rounded-lg">
                              <Users className="w-4 h-4 text-blue-600" />
                            </div>
                            <span className="font-semibold">{project.manager_name}</span>
                          </div>
                        )}
                        {project.start_date && project.end_date && (
                          <div className="flex items-center gap-2 text-sm text-gray-700">
                            <div className="p-1.5 bg-green-100 rounded-lg">
                              <Calendar className="w-4 h-4 text-green-600" />
                            </div>
                            <span>
                              {new Date(project.start_date).toLocaleDateString('zh-CN')} -{' '}
                              {new Date(project.end_date).toLocaleDateString('zh-CN')}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="space-y-2 pt-4 border-t border-gray-200">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 font-semibold flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-blue-500" />
                            进度
                          </span>
                          <span className="font-bold text-blue-600 text-lg">{project.progress_percent.toFixed(1)}%</span>
                        </div>
                        <div className="relative">
                          <div className="w-full bg-gray-200 rounded-full h-3 shadow-inner">
                            <div
                              className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 h-3 rounded-full transition-all duration-500 shadow-md"
                              style={{ width: `${project.progress_percent}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
