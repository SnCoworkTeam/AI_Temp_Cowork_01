'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, AlertTriangle, Filter } from 'lucide-react';

interface Risk {
  id: string;
  project_id: string;
  project_name: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  mitigation_plan: string;
  identified_date: string;
  created_at: string;
}

interface Project {
  id: string;
  name: string;
}

export default function RisksPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('project_id');
  const [risks, setRisks] = useState<Risk[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchProjects();
    fetchRisks();
  }, [selectedProject, severityFilter, statusFilter]);

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

  const fetchRisks = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      let url = `${apiUrl}/api/v1/risks`;
      const params = [];
      if (selectedProject && selectedProject !== 'all')
        params.push(`project_id=${selectedProject}`);
      if (severityFilter && severityFilter !== 'all') params.push(`severity=${severityFilter}`);
      if (statusFilter && statusFilter !== 'all') params.push(`status=${statusFilter}`);
      if (params.length > 0) url += '?' + params.join('&');
      const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (response.ok) setRisks((await response.json()).items || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-700 border-green-300',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      high: 'bg-orange-100 text-orange-700 border-orange-300',
      critical: 'bg-red-100 text-red-700 border-red-300',
    };
    return colors[severity] || colors.medium;
  };

  const getSeverityText = (severity: string) => {
    const texts: Record<string, string> = { low: '低', medium: '中', high: '高', critical: '严重' };
    return texts[severity] || severity;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      open: 'bg-red-100 text-red-700',
      monitoring: 'bg-yellow-100 text-yellow-700',
      mitigated: 'bg-green-100 text-green-700',
      closed: 'bg-gray-100 text-gray-700',
    };
    return colors[status] || colors.open;
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      open: '待处理',
      monitoring: '监控中',
      mitigated: '已缓解',
      closed: '已关闭',
    };
    return texts[status] || status;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">风险管理</h1>
          <p className="text-sm text-gray-600 font-medium mt-2">项目风险识别和管理</p>
        </div>
        <button className="px-4 py-2.5 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all duration-200 font-medium shadow-md hover:shadow-lg flex items-center gap-2">
          <Plus className="h-4 w-4" />
          新增风险
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有项目</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有严重程度</option>
            <option value="low">低</option>
            <option value="medium">中</option>
            <option value="high">高</option>
            <option value="critical">严重</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有状态</option>
            <option value="open">待处理</option>
            <option value="monitoring">监控中</option>
            <option value="mitigated">已缓解</option>
            <option value="closed">已关闭</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">加载中...</div>
      ) : risks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <AlertTriangle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">暂无风险</p>
          <button className="px-4 py-2.5 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all duration-200 font-medium shadow-md hover:shadow-lg">
            添加第一个风险
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {risks.map((r) => (
            <div
              key={r.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-red-300 transition-all duration-200 transition-shadow"
            >
              <div className="flex items-start gap-4">
                <AlertTriangle className="w-6 h-6 text-orange-600 flex-shrink-0 mt-2" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{r.title}</h3>
                    <div className="flex gap-2">
                      <span
                        className={`px-2.5 py-1 text-xs font-semibold rounded-full shadow-sm border ${getSeverityColor(r.severity)}`}
                      >
                        {getSeverityText(r.severity)}
                      </span>
                      <span
                        className={`px-2.5 py-1 text-xs font-semibold rounded-full shadow-sm ${getStatusColor(r.status)}`}
                      >
                        {getStatusText(r.status)}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 font-medium mb-3">{r.description}</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">项目:</span> {r.project_name}
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">识别日期:</span>{' '}
                      {new Date(r.identified_date).toLocaleDateString()}
                    </div>
                  </div>
                  {r.mitigation_plan && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <div className="text-sm font-medium text-gray-700 mb-1">缓解措施:</div>
                      <p className="text-sm text-gray-600 font-medium">{r.mitigation_plan}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">总风险数</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{risks.length}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">待处理</div>
          <div className="text-3xl font-bold text-red-600 mt-2">
            {risks.filter((r) => r.status === 'open').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">监控中</div>
          <div className="text-3xl font-bold text-yellow-600 mt-2">
            {risks.filter((r) => r.status === 'monitoring').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">高危风险</div>
          <div className="text-3xl font-bold text-orange-600 mt-2">
            {risks.filter((r) => r.severity === 'high' || r.severity === 'critical').length}
          </div>
        </div>
      </div>
    </div>
  );
}
