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
  Trash2,
  Eye,
  CheckCircle2,
} from 'lucide-react';
import Link from 'next/link';

interface WeeklyReport {
  id: string;
  project_id: string;
  project_name: string;
  week_start_date: string;
  week_end_date: string;
  progress_summary: string;
  completed_tasks: string;
  ongoing_tasks: string;
  planned_tasks: string;
  risks: string;
  progress_percent: number;
  created_at: string;
  updated_at: string;
  report_date?: string;
  week_number?: number;
  content_plan?: string;
  content_achievement?: string;
  issues_risks?: string;
  next_week_plan?: string;
}

interface Project {
  id: string;
  name: string;
  project_code: string;
}

export default function WeeklyReportsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState('all');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [editingReport, setEditingReport] = useState<WeeklyReport | null>(null);
  const [editFormData, setEditFormData] = useState({
    report_date: '',
    week_number: '',
    content_plan: '',
    content_achievement: '',
    issues_risks: '',
    next_week_plan: '',
  });
  const [saving, setSaving] = useState(false);

  // 初始化 selectedProject 从 URL 参数
  useEffect(() => {
    const projectId = searchParams?.get('project_id');
    if (projectId) {
      setSelectedProject(projectId);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchProjects();
    fetchReports();
  }, [selectedProject, selectedMonth]);

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

      let url = '/api/v1/weekly-reports';
      const params = [];
      if (selectedProject && selectedProject !== 'all') {
        params.push(`project_id=${selectedProject}`);
      }
      if (selectedMonth) {
        params.push(`month=${selectedMonth}`);
      }
      if (params.length > 0) {
        url += '?' + params.join('&');
      }

      const data = await apiGatewayClient.get<{ items: WeeklyReport[] }>(url);
      setReports(data.items || []);
    } catch (error: any) {
      console.error('获取周报列表失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const getWeekLabel = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    return `${start.getMonth() + 1}月${start.getDate()}日 - ${end.getMonth() + 1}月${end.getDate()}日`;
  };

  const handleEdit = (report: WeeklyReport) => {
    setEditingReport(report);
    setEditFormData({
      report_date:
        report.report_date || report.week_start_date || new Date().toISOString().split('T')[0],
      week_number: report.week_number?.toString() || '',
      content_plan: report.content_plan || report.ongoing_tasks || '',
      content_achievement: report.content_achievement || report.completed_tasks || '',
      issues_risks: report.issues_risks || report.risks || '',
      next_week_plan: report.next_week_plan || report.planned_tasks || '',
    });
  };

  const handleCancelEdit = () => {
    setEditingReport(null);
    setEditFormData({
      report_date: '',
      week_number: '',
      content_plan: '',
      content_achievement: '',
      issues_risks: '',
      next_week_plan: '',
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
      if (editFormData.report_date) payload.report_date = editFormData.report_date;
      if (editFormData.week_number) payload.week_number = parseInt(editFormData.week_number);
      if (editFormData.content_plan !== undefined) payload.content_plan = editFormData.content_plan;
      if (editFormData.content_achievement !== undefined)
        payload.content_achievement = editFormData.content_achievement;
      if (editFormData.issues_risks !== undefined) payload.issues_risks = editFormData.issues_risks;
      if (editFormData.next_week_plan !== undefined)
        payload.next_week_plan = editFormData.next_week_plan;

      await apiGatewayClient.put(`/api/v1/weekly-reports/${editingReport.id}`, payload);
      await fetchReports();
      handleCancelEdit();
    } catch (error: any) {
      console.error('更新周报失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      } else {
        alert(error?.message || '更新周报失败');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm('确定要删除这份周报吗？')) return;

    try {
      if (!isAuthenticated()) {
        router.push('/login');
        return;
      }
      await apiGatewayClient.delete(`/api/v1/weekly-reports/${reportId}`);
      await fetchReports();
    } catch (error: any) {
      console.error('删除周报失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      } else {
        alert(error?.message || '删除周报失败');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面头部 - 美化 */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl shadow-xl border-2 border-blue-200 p-6 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500 rounded-xl shadow-lg">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">周报管理</h1>
              <p className="text-gray-600 mt-1 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                项目周报提交和查看
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/projects/weekly-reports/create')}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 flex items-center gap-2 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <Plus className="h-5 w-5" />
              创建周报
            </button>
          </div>
        </div>
      </div>

      {/* 统计卡片 - 移到顶部 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl shadow-lg border-2 border-blue-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-md">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <TrendingUp className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-sm font-semibold text-blue-700 mb-1">总周报数</div>
          <div className="text-4xl font-bold text-blue-600">{reports.length}</div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl shadow-lg border-2 border-green-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-md">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <CheckCircle2 className="w-5 h-5 text-green-400" />
          </div>
          <div className="text-sm font-semibold text-green-700 mb-1">平均进度</div>
          <div className="text-4xl font-bold text-green-600">
            {reports.length > 0
              ? (
                  reports.reduce((sum, r) => sum + r.progress_percent, 0) / reports.length
                ).toFixed(0)
              : 0}
            %
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-2xl shadow-lg border-2 border-orange-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-md">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <AlertCircle className="w-5 h-5 text-orange-400" />
          </div>
          <div className="text-sm font-semibold text-orange-700 mb-1">有风险项目</div>
          <div className="text-4xl font-bold text-orange-600">
            {reports.filter((r) => r.risks && r.risks.length > 0).length}
          </div>
        </div>
      </div>

      {/* 过滤器 - 美化 */}
      <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-6">
        <div className="flex items-center gap-2 text-gray-700 font-bold mb-5">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Filter className="w-5 h-5 text-blue-600" />
          </div>
          <span className="text-lg">筛选条件</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 项目过滤 */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">项目</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
            >
              <option value="all">所有项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>

          {/* 月份过滤 */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">月份</label>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
            />
          </div>
        </div>
      </div>

      {/* 周报列表 */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 mb-4">
            <Calendar className="h-10 w-10 text-gray-400" />
          </div>
          <p className="text-gray-600 font-semibold text-lg mb-2">暂无周报</p>
          <p className="text-sm text-gray-500 mb-6">开始创建您的第一份周报</p>
          <button
            onClick={() => router.push('/projects/weekly-reports/create')}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            创建第一份周报
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="group relative bg-white rounded-2xl shadow-lg border-2 border-gray-200 p-6 hover:shadow-2xl hover:border-blue-400 transition-all duration-300 cursor-pointer overflow-hidden transform hover:scale-[1.02]"
            >
              {/* 顶部渐变装饰条 */}
              <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>

              <div className="flex flex-col space-y-4">
                {/* 标题行 */}
                <div className="flex items-center justify-between mb-4">
                  <Link
                    href={`/projects/weekly-reports/${report.id}`}
                    className="flex items-center gap-4 flex-1"
                  >
                    <div className="p-3 bg-gradient-to-br from-blue-100 to-indigo-200 rounded-xl shadow-md group-hover:from-blue-200 group-hover:to-indigo-300 transition-colors">
                      <Calendar className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {report.project_name} - 周报
                      </h3>
                      <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {getWeekLabel(report.week_start_date, report.week_end_date)}
                      </p>
                    </div>
                  </Link>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-200 shadow-sm">
                      <TrendingUp className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-bold text-green-700">
                        进度: {report.progress_percent.toFixed(0)}%
                      </span>
                    </div>
                    <Link
                      href={`/projects/weekly-reports/${report.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors z-10 relative"
                      title="查看周报"
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
                      title="编辑周报"
                    >
                      <Edit className="w-5 h-5" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        if (confirm('确定要删除这份周报吗？')) {
                          handleDelete(report.id);
                        }
                      }}
                      className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors z-10 relative"
                      title="删除周报"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* 进度条 */}
                <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden mb-4">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-2.5 rounded-full transition-all duration-500 shadow-sm"
                    style={{ width: `${report.progress_percent}%` }}
                  />
                </div>

                {/* 详细信息 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* 进度概要 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <TrendingUp className="w-4 h-4" />
                      <span>进度概要</span>
                    </div>
                    <p className="text-sm text-gray-600 pl-6 line-clamp-3">
                      {report.progress_summary || '暂无内容'}
                    </p>
                  </div>

                  {/* 已完成任务 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <FileText className="w-4 h-4" />
                      <span>已完成任务</span>
                    </div>
                    <p className="text-sm text-gray-600 pl-6 line-clamp-3">
                      {report.completed_tasks || '暂无内容'}
                    </p>
                  </div>

                  {/* 进行中任务 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <FileText className="w-4 h-4" />
                      <span>进行中任务</span>
                    </div>
                    <p className="text-sm text-gray-600 pl-6 line-clamp-3">
                      {report.ongoing_tasks || '暂无内容'}
                    </p>
                  </div>

                  {/* 计划任务 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <FileText className="w-4 h-4" />
                      <span>下周计划</span>
                    </div>
                    <p className="text-sm text-gray-600 pl-6 line-clamp-3">
                      {report.planned_tasks || '暂无内容'}
                    </p>
                  </div>
                </div>

                {/* 风险问题 */}
                {report.risks && (
                  <div className="border-t border-gray-200 pt-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-orange-700 mb-2">
                      <AlertTriangle className="w-4 h-4" />
                      <span>风险和问题</span>
                    </div>
                    <p className="text-sm text-gray-600 pl-6 line-clamp-2">{report.risks}</p>
                  </div>
                )}

                {/* 时间戳 */}
                <div className="text-xs text-gray-500 border-t border-gray-200 pt-3">
                  创建时间: {new Date(report.created_at).toLocaleString()} | 更新时间:{' '}
                  {new Date(report.updated_at).toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 编辑模态框 */}
      {editingReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-8 py-5 border-b-2 border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-md">
                  <Edit className="w-5 h-5 text-white" />
                </div>
                编辑周报
              </h2>
              <button
                onClick={handleCancelEdit}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">报告日期</label>
                  <input
                    type="date"
                    value={editFormData.report_date}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, report_date: e.target.value })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">周数</label>
                  <input
                    type="number"
                    min="1"
                    max="53"
                    value={editFormData.week_number}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, week_number: e.target.value })
                    }
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
                    placeholder="可选，如：1-53"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">本周计划内容</label>
                <textarea
                  value={editFormData.content_plan}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, content_plan: e.target.value })
                  }
                  rows={5}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="描述本周计划完成的工作内容..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">本周完成成果</label>
                <textarea
                  value={editFormData.content_achievement}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, content_achievement: e.target.value })
                  }
                  rows={5}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="描述本周实际完成的工作成果..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">问题与风险</label>
                <textarea
                  value={editFormData.issues_risks}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, issues_risks: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="描述本周遇到的问题和风险..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">下周计划</label>
                <textarea
                  value={editFormData.next_week_plan}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, next_week_plan: e.target.value })
                  }
                  rows={5}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
                  placeholder="描述下周计划完成的工作内容..."
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
                className="px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
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

