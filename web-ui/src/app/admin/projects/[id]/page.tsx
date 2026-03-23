'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import {
  ArrowLeft,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Users,
  Clock,
  FileText,
} from 'lucide-react';
import Link from 'next/link';
import ProjectPhaseProgress from '@/components/ProjectPhaseProgress';

interface Project {
  id: string;
  project_code: string;
  name: string;
  description: string;
  status: string;
  priority: string;
  start_date: string;
  end_date: string;
  progress_percent: number;
  health_score: number;
  created_at: string;
  updated_at: string;
  requires_weekly_report?: boolean;
}

interface Task {
  id: string;
  name: string;
  status: string;
  progress_percent: number;
}

interface Milestone {
  id: string;
  name: string;
  status: string;
  target_date: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (projectId) {
      fetchProjectData();
    }
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProject(data);
      } else {
        setError('获取项目详情失败');
      }
    } catch (error) {
      console.error('获取项目详情失败:', error);
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-gray-100 text-gray-700 border-gray-300',
      active: 'bg-blue-100 text-blue-700 border-blue-300',
      delayed: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      completed: 'bg-green-100 text-green-700 border-green-300',
      cancelled: 'bg-red-100 text-red-700 border-red-300',
    };
    return colors[status] || colors.planning;
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      planning: '规划中',
      active: '进行中',
      delayed: '已延迟',
      completed: '已完成',
      cancelled: '已取消',
    };
    return texts[status] || status;
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'bg-gray-100 text-gray-600',
      medium: 'bg-blue-100 text-blue-600',
      high: 'bg-orange-100 text-orange-600',
      critical: 'bg-red-100 text-red-600',
    };
    return colors[priority] || colors.medium;
  };

  const getPriorityText = (priority: string) => {
    const texts: Record<string, string> = {
      low: '低',
      medium: '中',
      high: '高',
      critical: '紧急',
    };
    return texts[priority] || priority;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || '项目不存在'}
        </div>
        <Link href="/admin/projects" className="inline-block mt-4 text-blue-600 hover:underline">
          返回项目列表
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* 返回按钮和标题 */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600 mt-1">{project.project_code}</p>
        </div>
        <div className="flex gap-2">
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(project.status)}`}
          >
            {getStatusText(project.status)}
          </span>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(project.priority)}`}
          >
            {getPriorityText(project.priority)}
          </span>
        </div>
      </div>

      {/* 项目概述卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6 md:col-span-2">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">项目阶段</p>
              <p className="text-xs text-gray-500 mt-0.5">当前项目进度阶段</p>
            </div>
          </div>
          <ProjectPhaseProgress
            currentPhase={(() => {
              // 从项目分类中获取项目阶段
              if (project.basic_data_categories && project.basic_data_categories.length > 0) {
                const phaseCategory = project.basic_data_categories.find(
                  (cat) => cat.category_type === 'project_phase'
                );
                if (phaseCategory) {
                  // 优先使用ID，如果没有ID则使用code或name
                  return phaseCategory.id || phaseCategory.code || phaseCategory.name;
                }
              }
              return undefined;
            })()}
            className="py-2"
          />
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">健康度</p>
              <p className="text-2xl font-bold text-gray-900">{project.health_score.toFixed(0)}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Calendar className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">开始日期</p>
              <p className="text-sm font-medium text-gray-900">
                {project.start_date ? new Date(project.start_date).toLocaleDateString() : '-'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-orange-100 rounded-lg">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">结束日期</p>
              <p className="text-sm font-medium text-gray-900">
                {project.end_date ? new Date(project.end_date).toLocaleDateString() : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 项目阶段进度 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl shadow-sm">
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">项目阶段</h2>
        </div>
        <ProjectPhaseProgress
          currentPhase={(() => {
            // 从项目分类中获取项目阶段
            if (project.basic_data_categories && project.basic_data_categories.length > 0) {
              const phaseCategory = project.basic_data_categories.find(
                (cat) => cat.category_type === 'project_phase'
              );
              if (phaseCategory) {
                // 优先使用ID，如果没有ID则使用code或name
                return phaseCategory.id || phaseCategory.code || phaseCategory.name;
              }
            }
            return undefined;
          })()}
        />
      </div>

      {/* 项目描述 */}
      {project.description && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">项目描述</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{project.description}</p>
        </div>
      )}

      {/* 项目设置 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">项目设置</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">是否编写周报</span>
            <span className="text-sm font-medium text-gray-900">
              {project.requires_weekly_report ? (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  是
                </span>
              ) : (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  否
                </span>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* 快速链接 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">相关功能</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link
            href={`/admin/projects/tasks?project_id=${project.id}`}
            className="flex items-center gap-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <CheckCircle className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium">任务管理</span>
          </Link>
          <Link
            href={`/admin/projects/milestones?project_id=${project.id}`}
            className="flex items-center gap-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Calendar className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium">里程碑</span>
          </Link>
          <Link
            href={`/admin/projects/weekly-reports?project_id=${project.id}`}
            className="flex items-center gap-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FileText className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium">周报</span>
          </Link>
          <Link
            href={`/admin/projects/risks?project_id=${project.id}`}
            className="flex items-center gap-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span className="text-sm font-medium">风险管理</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
