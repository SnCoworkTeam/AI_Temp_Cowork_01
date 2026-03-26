'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getAccessToken, isAuthenticated } from '@/lib/auth';
import { apiGatewayClient } from '@/lib/api/client';
import ErrorMessage from '@/components/ErrorMessage';
import {
  Plus,
  Calendar,
  TrendingUp,
  AlertTriangle,
  AlertCircle,
  FileText,
  Filter,
  Edit,
  X,
  Save,
  Eye,
  Trash2,
  CheckCircle2,
} from 'lucide-react';
import Link from 'next/link';

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
      if (!isAuthenticated()) {
        router.push('/login');
        return;
      }
      const data = await apiGatewayClient.get<{ items: Project[] }>('/api/v1/projects?limit=1000');
      setProjects(data.items || []);
    } catch (error: any) {
      console.error('获取项目列表失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      }
    }
  };

  const fetchReports = async () => {
    try {
      setLoading(true);
      if (!isAuthenticated()) {
        router.push('/login');
        return;
      }

      let url = '/api/v1/monthly-reports';
      const params = [];
      if (selectedProject && selectedProject !== 'all')
        params.push(`project_id=${selectedProject}`);
      if (selectedYear) params.push(`year=${selectedYear}`);
      if (params.length > 0) url += '?' + params.join('&');

      const data = await apiGatewayClient.get<{ items: MonthlyReport[] }>(url);
      const items = (data.items || []).map((r: any) => ({
        ...r,
        month: r.report_month || r.month || '',
        progress_percent: typeof r.progress_percent === 'number' ? r.progress_percent : 0,
      }));
      setReports(items);
    } catch (error: any) {
      console.error('获取月报列表失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      }
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
      if (!isAuthenticated()) {
        router.push('/login');
        return;
      }

      const payload: any = {};
      if (editFormData.summary !== undefined) payload.summary = editFormData.summary;
      if (editFormData.achievements !== undefined) payload.achievements = editFormData.achievements;
      if (editFormData.challenges !== undefined) payload.challenges = editFormData.challenges;
      if (editFormData.next_month_plan !== undefined)
        payload.next_month_plan = editFormData.next_month_plan;

      await apiGatewayClient.put(`/api/v1/monthly-reports/${editingReport.id}`, payload);
      await fetchReports();
      handleCancelEdit();
    } catch (error: any) {
      console.error('更新月报失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      } else {
        alert(error?.message || '更新月报失败');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm('确定要删除这份月报吗？')) return;

    try {
      if (!isAuthenticated()) {
        router.push('/login');
        return;
      }
      await apiGatewayClient.delete(`/api/v1/monthly-reports/${reportId}`);
      await fetchReports();
    } catch (error: any) {
      console.error('删除月报失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      } else {
        alert(error?.message || '删除月报失败');
      }
    }
  };

  // 计算统计数据
  const stats = {
    totalReports: reports.length,
    averageProgress: reports.length > 0
      ? reports.reduce((sum, r) => sum + (r.progress_percent ?? 0), 0) / reports.length
      : 0,
    reportsWithChallenges: reports.filter((r) => r.challenges && r.challenges.length > 0).length,
  };

  return (
    <div className="space-y-6">
      {/* 页面头部 - 美化 */}
      <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 rounded-2xl shadow-xl border-2 border-purple-200 p-6 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-500 rounded-xl shadow-lg">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">月报管理</h1>
              <p className="text-gray-600 mt-1 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                项目月报提交和查看
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/projects/monthly-reports/create')}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 text-white rounded-xl hover:from-purple-700 hover:via-pink-700 hover:to-rose-700 transition-all duration-200 flex items-center gap-2 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <Plus className="h-5 w-5" />
              创建月报
            </button>
          </div>
        </div>
      </div>

      {/* 统计卡片 - 移到顶部 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl shadow-lg border-2 border-purple-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-md">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <TrendingUp className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-sm font-semibold text-purple-700 mb-1">总月报数</div>
          <div className="text-4xl font-bold text-purple-600">{stats.totalReports}</div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl shadow-lg border-2 border-green-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-md">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <CheckCircle2 className="w-5 h-5 text-green-400" />
          </div>
          <div className="text-sm font-semibold text-green-700 mb-1">平均进度</div>
          <div className="text-4xl font-bold text-green-600">{stats.averageProgress.toFixed(0)}%</div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-2xl shadow-lg border-2 border-orange-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-md">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <AlertCircle className="w-5 h-5 text-orange-400" />
          </div>
          <div className="text-sm font-semibold text-orange-700 mb-1">有挑战项目</div>
          <div className="text-4xl font-bold text-orange-600">{stats.reportsWithChallenges}</div>
        </div>
      </div>

      {/* 过滤器 - 美化 */}
      <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-6">
        <div className="flex items-center gap-2 text-gray-700 font-bold mb-5">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Filter className="w-5 h-5 text-purple-600" />
          </div>
          <span className="text-lg">筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">项目</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-white text-sm"
            >
              <option value="all">所有项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">年份</label>
            <input
              type="number"
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              min="2020"
              max="2030"
              placeholder="年份"
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-white text-sm"
            />
          </div>
        </div>
      </div>

      {/* 月报列表 */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 mb-4">
            <Calendar className="h-10 w-10 text-gray-400" />
          </div>
          <p className="text-gray-600 font-semibold text-lg mb-2">暂无月报</p>
          <p className="text-sm text-gray-500 mb-6">开始创建您的第一份月报</p>
          <button
            onClick={() => router.push('/projects/monthly-reports/create')}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            创建第一份月报
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="group relative bg-white rounded-2xl shadow-lg border-2 border-gray-200 p-6 hover:shadow-2xl hover:border-purple-400 transition-all duration-300 cursor-pointer overflow-hidden transform hover:scale-[1.02]"
            >
              {/* 顶部渐变装饰条 */}
              <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-purple-500 via-pink-500 to-rose-500"></div>

              <div className="flex flex-col space-y-4">
                {/* 标题行 */}
                <div className="flex items-center justify-between mb-4">
                  <Link
                    href={`/projects/monthly-reports/${report.id}`}
                    className="flex items-center gap-4 flex-1"
                  >
                    <div className="p-3 bg-gradient-to-br from-purple-100 to-pink-200 rounded-xl shadow-md group-hover:from-purple-200 group-hover:to-pink-300 transition-colors">
                      <Calendar className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-900 group-hover:text-purple-600 transition-colors">
                        {report.project_name || '未命名项目'} -{' '}
                        {report.month || report.report_month || ''}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {report.month || report.report_month || ''}
                      </p>
                    </div>
                  </Link>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-200 shadow-sm">
                      <TrendingUp className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-bold text-green-700">
                        进度: {(report.progress_percent ?? 0).toFixed(0)}%
                      </span>
                    </div>
                    <Link
                      href={`/projects/monthly-reports/${report.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors z-10 relative"
                      title="查看月报"
                    >
                      <Eye className="w-5 h-5" />
                    </Link>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        handleEdit(report);
                      }}
                      className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors z-10 relative"
                      title="编辑月报"
                    >
                      <Edit className="w-5 h-5" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        if (confirm('确定要删除这份月报吗？')) {
                          handleDelete(report.id);
                        }
                      }}
                      className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors z-10 relative"
                      title="删除月报"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* 进度条 */}
                <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden mb-4">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-pink-600 h-2.5 rounded-full transition-all duration-500 shadow-sm"
                    style={{ width: `${report.progress_percent ?? 0}%` }}
                  />
                </div>

                {/* 详细信息 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* 月度总结 */}
                  {report.summary && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <FileText className="w-4 h-4" />
                        <span>月度总结</span>
                      </div>
                      <p className="text-sm text-gray-600 pl-6 line-clamp-3">{report.summary}</p>
                    </div>
                  )}

                  {/* 主要成果 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <TrendingUp className="w-4 h-4" />
                      <span>主要成果</span>
                    </div>
                    <p className="text-sm text-gray-600 pl-6 line-clamp-3">
                      {report.achievements || '暂无内容'}
                    </p>
                  </div>

                  {/* 挑战与问题 */}
                  {report.challenges && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-orange-700">
                        <AlertTriangle className="w-4 h-4" />
                        <span>挑战与问题</span>
                      </div>
                      <p className="text-sm text-gray-600 pl-6 line-clamp-3">{report.challenges}</p>
                    </div>
                  )}

                  {/* 下月计划 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <Calendar className="w-4 h-4" />
                      <span>下月计划</span>
                    </div>
                    <p className="text-sm text-gray-600 pl-6 line-clamp-3">
                      {report.next_month_plan || '暂无内容'}
                    </p>
                  </div>
                </div>

                {/* 时间戳 */}
                {report.created_at && (
                  <div className="text-xs text-gray-500 border-t border-gray-200 pt-3">
                    创建时间: {new Date(report.created_at).toLocaleString('zh-CN')}
                    {report.updated_at &&
                      ` | 更新时间: ${new Date(report.updated_at).toLocaleString('zh-CN')}`}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 编辑模态框 */}
      {editingReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 px-8 py-5 border-b-2 border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg shadow-md">
                  <Edit className="w-5 h-5 text-white" />
                </div>
                编辑月报
              </h2>
              <button
                onClick={handleCancelEdit}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">月度总结</label>
                <textarea
                  value={editFormData.summary}
                  onChange={(e) => setEditFormData({ ...editFormData, summary: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="本月项目进展总结..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">主要成果</label>
                <textarea
                  value={editFormData.achievements}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, achievements: e.target.value })
                  }
                  rows={5}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="描述本月完成的主要工作成果..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">挑战与问题</label>
                <textarea
                  value={editFormData.challenges}
                  onChange={(e) => setEditFormData({ ...editFormData, challenges: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="描述本月遇到的挑战和问题..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">下月计划</label>
                <textarea
                  value={editFormData.next_month_plan}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, next_month_plan: e.target.value })
                  }
                  rows={5}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="描述下月计划完成的工作内容..."
                />
              </div>
            </div>
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-t-2 border-gray-200 flex justify-end gap-3 sticky bottom-0">
              <button
                type="button"
                onClick={handleCancelEdit}
                disabled={saving}
                className="px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm hover:shadow-md disabled:opacity-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={saving}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 text-white rounded-xl hover:from-purple-700 hover:via-pink-700 hover:to-rose-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                <Save className="h-5 w-5" />
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

