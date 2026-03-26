'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import {
  Plus,
  Calendar,
  TrendingUp,
  AlertTriangle,
  FileText,
  Filter,
  Edit,
  X,
  Save,
} from 'lucide-react';

interface MonthlyReport {
  id: string;
  project_id: string;
  project_name?: string;
  month: string;
  report_month?: string;
  summary?: string;
  achievements?: string;
  challenges?: string;
  next_month_plan?: string;
  progress_percent?: number;
  created_at?: string;
  updated_at?: string;
}

interface Project {
  id: string;
  name: string;
}

export default function MonthlyReportsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('project_id');

  const [reports, setReports] = useState<MonthlyReport[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());
  const [editingReport, setEditingReport] = useState<MonthlyReport | null>(null);
  const [editFormData, setEditFormData] = useState({
    summary: '',
    achievements: '',
    challenges: '',
    next_month_plan: '',
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchProjects();
    fetchReports();
  }, [selectedProject, selectedYear]);

  const fetchProjects = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      const response = await fetch(`${apiUrl}/api/v1/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data.items || []);
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
    }
  };

  const fetchReports = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      let url = `${apiUrl}/api/v1/monthly-reports`;
      const params = [];
      if (selectedProject && selectedProject !== 'all')
        params.push(`project_id=${selectedProject}`);
      if (selectedYear) params.push(`year=${selectedYear}`);
      if (params.length > 0) url += '?' + params.join('&');
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        const items = (data.items || []).map((r: any) => ({
          ...r,
          month: r.report_month || r.month || '',
          progress_percent: typeof r.progress_percent === 'number' ? r.progress_percent : 0,
        }));
        setReports(items);
      }
    } catch (error) {
      console.error('获取月报列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (report: MonthlyReport) => {
    setEditingReport(report);
    setEditFormData({
      summary: report.summary || '',
      achievements: report.achievements || '',
      challenges: report.challenges || '',
      next_month_plan: report.next_month_plan || '',
    });
  };

  const handleCancelEdit = () => {
    setEditingReport(null);
    setEditFormData({
      summary: '',
      achievements: '',
      challenges: '',
      next_month_plan: '',
    });
  };

  const handleSaveEdit = async () => {
    if (!editingReport) return;

    try {
      setSaving(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const payload: any = {};
      if (editFormData.summary !== undefined) payload.summary = editFormData.summary;
      if (editFormData.achievements !== undefined) payload.achievements = editFormData.achievements;
      if (editFormData.challenges !== undefined) payload.challenges = editFormData.challenges;
      if (editFormData.next_month_plan !== undefined)
        payload.next_month_plan = editFormData.next_month_plan;

      const response = await fetch(`${apiUrl}/api/v1/monthly-reports/${editingReport.id}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        await fetchReports();
        handleCancelEdit();
      } else {
        const error = await response.json();
        alert(error.detail || '更新月报失败');
      }
    } catch (error) {
      console.error('更新月报失败:', error);
      alert('更新月报失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">月报管理</h1>
          <p className="text-gray-600 mt-1">项目月报提交和查看</p>
        </div>
        <button
          onClick={() => router.push('/admin/projects/monthly-reports/create')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          创建月报
        </button>
      </div>

      <div className="bg-white rounded-lg shadow border border-gray-200 p-4 space-y-4">
        <div className="flex items-center gap-2 text-gray-700 font-medium">
          <Filter className="w-4 h-4" />
          <span>筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">所有项目</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            min="2020"
            max="2030"
            placeholder="年份"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center text-gray-500">
          加载中...
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">暂无月报</p>
          <button className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            创建第一份月报
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="bg-white rounded-lg shadow border border-gray-200 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-blue-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {report.project_name || '未命名项目'} -{' '}
                      {report.month || report.report_month || ''}
                    </h3>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-sm font-medium text-gray-900">
                    进度: {(report.progress_percent ?? 0).toFixed(0)}%
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(report);
                    }}
                    className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors z-10 relative"
                    title="编辑月报"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${report.progress_percent ?? 0}%` }}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">成果:</span>{' '}
                  <p className="text-gray-600 mt-1 line-clamp-2">{report.achievements || '暂无'}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">挑战:</span>{' '}
                  <p className="text-gray-600 mt-1 line-clamp-2">{report.challenges || '暂无'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 编辑模态框 */}
      {editingReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <div className="w-1 h-5 bg-blue-600 rounded-full"></div>
                编辑月报
              </h2>
              <button
                onClick={handleCancelEdit}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">月度总结</label>
                <textarea
                  value={editFormData.summary}
                  onChange={(e) => setEditFormData({ ...editFormData, summary: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="本月项目进展总结..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">主要成果</label>
                <textarea
                  value={editFormData.achievements}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, achievements: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="描述本月完成的主要工作成果..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">挑战与问题</label>
                <textarea
                  value={editFormData.challenges}
                  onChange={(e) => setEditFormData({ ...editFormData, challenges: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="描述本月遇到的挑战和问题..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">下月计划</label>
                <textarea
                  value={editFormData.next_month_plan}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, next_month_plan: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="描述下月计划完成的工作内容..."
                />
              </div>
            </div>
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                type="button"
                onClick={handleCancelEdit}
                disabled={saving}
                className="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm disabled:opacity-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={saving}
                className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-md hover:shadow-lg"
              >
                <Save className="h-4 w-4" />
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
