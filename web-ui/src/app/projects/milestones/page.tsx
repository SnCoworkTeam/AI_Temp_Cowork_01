'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, Target, CheckCircle, Clock, AlertCircle, Filter } from 'lucide-react';

interface Milestone {
  id: string;
  project_id: string;
  project_name: string;
  name: string;
  description: string;
  status: string;
  target_date: string;
  completion_date: string;
  created_at: string;
}

interface Project {
  id: string;
  name: string;
}

export default function MilestonesPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('project_id');
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchProjects();
    fetchMilestones();
  }, [selectedProject, statusFilter]);

  const fetchProjects = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      const response = await fetch(`${apiUrl}/api/v1/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) setProjects((await response.json()).items || []);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchMilestones = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      let url = `${apiUrl}/api/v1/milestones`;
      const params = [];
      if (selectedProject && selectedProject !== 'all')
        params.push(`project_id=${selectedProject}`);
      if (statusFilter && statusFilter !== 'all') params.push(`status=${statusFilter}`);
      if (params.length > 0) url += '?' + params.join('&');
      const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (response.ok) setMilestones((await response.json()).items || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (status === 'in_progress') return <Clock className="w-5 h-5 text-blue-600" />;
    return <AlertCircle className="w-5 h-5 text-gray-600" />;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-700 border-gray-300',
      in_progress: 'bg-blue-100 text-blue-700 border-blue-300',
      completed: 'bg-green-100 text-green-700 border-green-300',
      delayed: 'bg-red-100 text-red-700 border-red-300',
    };
    return colors[status] || colors.pending;
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待开始',
      in_progress: '进行中',
      completed: '已完成',
      delayed: '已延迟',
    };
    return texts[status] || status;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">里程碑管理</h1>
          <p className="text-sm text-gray-600 mt-1">项目关键里程碑跟踪</p>
        </div>
        <button className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 flex items-center gap-2 font-medium shadow-md hover:shadow-lg">
          <Plus className="h-4 w-4" />
          新建里程碑
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="flex items-center gap-2 text-gray-700 font-semibold mb-4">
          <div className="p-1.5 bg-blue-100 rounded-lg">
            <Filter className="w-4 h-4 text-blue-600" />
          </div>
          <span>筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有项目</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有状态</option>
            <option value="pending">待开始</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
            <option value="delayed">已延迟</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : milestones.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
            <Target className="h-8 w-8 text-gray-400" />
          </div>
          <p className="text-gray-600 font-medium mb-2">暂无里程碑</p>
          <p className="text-sm text-gray-500 mb-6">开始创建您的第一个里程碑</p>
          <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm">
            <Plus className="h-4 w-4" />
            创建第一个里程碑
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {milestones.map((m) => (
            <div
              key={m.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all duration-200"
            >
              <div className="flex items-start gap-4">
                <div className="p-2 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg shadow-sm flex-shrink-0">
                  {getStatusIcon(m.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2 gap-2">
                    <h3 className="text-lg font-semibold text-gray-900 truncate">{m.name}</h3>
                    <span
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full border shadow-sm flex-shrink-0 ${getStatusColor(m.status)}`}
                    >
                      {getStatusText(m.status)}
                    </span>
                  </div>
                  {m.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">{m.description}</p>
                  )}
                  <div className="text-sm text-gray-500 space-y-1.5">
                    <div className="flex items-center gap-1">
                      <span className="font-medium">项目:</span> {m.project_name}
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="font-medium">目标日期:</span>{' '}
                      {new Date(m.target_date).toLocaleDateString('zh-CN')}
                    </div>
                    {m.completion_date && (
                      <div className="flex items-center gap-1">
                        <span className="font-medium">完成日期:</span>{' '}
                        {new Date(m.completion_date).toLocaleDateString('zh-CN')}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">总里程碑数</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{milestones.length}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">进行中</div>
          <div className="text-3xl font-bold text-blue-600 mt-2">
            {milestones.filter((m) => m.status === 'in_progress').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">已完成</div>
          <div className="text-3xl font-bold text-green-600 mt-2">
            {milestones.filter((m) => m.status === 'completed').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">已延迟</div>
          <div className="text-3xl font-bold text-red-600 mt-2">
            {milestones.filter((m) => m.status === 'delayed').length}
          </div>
        </div>
      </div>
    </div>
  );
}
