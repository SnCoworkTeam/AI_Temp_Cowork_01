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
  const projectId = searchParams?.get('project_id');

  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');
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

  useEffect(() => {
    fetchProjects();
    fetchReports();
  }, [selectedProject, selectedMonth]);

  const fetchProjects = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects`, {
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
    }
  };

  const fetchReports = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      let url = `${apiUrl}/api/v1/weekly-reports`;
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

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setReports(data.items || []);
      }
    } catch (error) {
      console.error('获取周报列表失败:', error);
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
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const payload: any = {};
      if (editFormData.report_date) payload.report_date = editFormData.report_date;
      if (editFormData.week_number) payload.week_number = parseInt(editFormData.week_number);
      if (editFormData.content_plan !== undefined) payload.content_plan = editFormData.content_plan;
      if (editFormData.content_achievement !== undefined)
        payload.content_achievement = editFormData.content_achievement;
      if (editFormData.issues_risks !== undefined) payload.issues_risks = editFormData.issues_risks;
      if (editFormData.next_week_plan !== undefined)
        payload.next_week_plan = editFormData.next_week_plan;

      const response = await fetch(`${apiUrl}/api/v1/weekly-reports/${editingReport.id}`, {
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
        alert(error.detail || '更新周报失败');
      }
    } catch (error) {
      console.error('更新周报失败:', error);
      alert('更新周报失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 标题和操作按钮 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5 hover:shadow-md transition-shadow">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">周报管理</h1>
          <p className="text-sm text-gray-600 font-medium mt-2">项目周报提交和查看</p>
        </div>
        <button
          onClick={() => router.push('/admin/projects/weekly-reports/create')}
          className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-md hover:shadow-lg flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          创建周报
        </button>
      </div>

      {/* 过滤器 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="flex items-center gap-2 text-gray-700 font-semibold mb-4">
          <div className="p-1.5 bg-blue-100 rounded-lg">
            <Filter className="w-4 h-4 text-blue-600" />
          </div>
          <span>筛选条件</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 hover:shadow-md transition-shadow">
          {/* 项目过滤 */}
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有项目</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>

          {/* 月份过滤 */}
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
          />
        </div>
      </div>

      {/* 周报列表 */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-500">
          加载中...
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">暂无周报</p>
          <button className="inline-block px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-md hover:shadow-lg">
            创建第一份周报
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all duration-200 transition-shadow"
            >
              <div className="flex flex-col space-y-4">
                {/* 标题行 */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-5 hover:shadow-md transition-shadow">
                    <Calendar className="w-5 h-5 text-blue-600" />
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {report.project_name} - 周报
                      </h3>
                      <p className="text-sm text-gray-600 font-medium">
                        {getWeekLabel(report.week_start_date, report.week_end_date)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-900">
                        进度: {report.progress_percent.toFixed(0)}%
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(report);
                      }}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors z-10 relative"
                      title="编辑周报"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* 进度条 */}
                <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-2.5 rounded-full transition-all duration-500 shadow-sm transition-all"
                    style={{ width: `${report.progress_percent}%` }}
                  />
                </div>

                {/* 详细信息 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 hover:shadow-md transition-shadow">
                  {/* 进度概要 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <TrendingUp className="w-4 h-4" />
                      <span>进度概要</span>
                    </div>
                    <p className="text-sm text-gray-600 font-medium pl-6 line-clamp-3">
                      {report.progress_summary || '暂无内容'}
                    </p>
                  </div>

                  {/* 已完成任务 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <FileText className="w-4 h-4" />
                      <span>已完成任务</span>
                    </div>
                    <p className="text-sm text-gray-600 font-medium pl-6 line-clamp-3">
                      {report.completed_tasks || '暂无内容'}
                    </p>
                  </div>

                  {/* 进行中任务 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <FileText className="w-4 h-4" />
                      <span>进行中任务</span>
                    </div>
                    <p className="text-sm text-gray-600 font-medium pl-6 line-clamp-3">
                      {report.ongoing_tasks || '暂无内容'}
                    </p>
                  </div>

                  {/* 计划任务 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <FileText className="w-4 h-4" />
                      <span>下周计划</span>
                    </div>
                    <p className="text-sm text-gray-600 font-medium pl-6 line-clamp-3">
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
                    <p className="text-sm text-gray-600 font-medium pl-6 line-clamp-2">
                      {report.risks}
                    </p>
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <div className="w-1 h-5 bg-blue-600 rounded-full"></div>
                编辑周报
              </h2>
              <button
                onClick={handleCancelEdit}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">报告日期</label>
                  <input
                    type="date"
                    value={editFormData.report_date}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, report_date: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">周数</label>
                  <input
                    type="number"
                    min="1"
                    max="53"
                    value={editFormData.week_number}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, week_number: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                    placeholder="可选，如：1-53"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">本周计划内容</label>
                <textarea
                  value={editFormData.content_plan}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, content_plan: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="描述本周计划完成的工作内容..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">本周完成成果</label>
                <textarea
                  value={editFormData.content_achievement}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, content_achievement: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="描述本周实际完成的工作成果..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">问题与风险</label>
                <textarea
                  value={editFormData.issues_risks}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, issues_risks: e.target.value })
                  }
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="描述本周遇到的问题和风险..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">下周计划</label>
                <textarea
                  value={editFormData.next_week_plan}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, next_week_plan: e.target.value })
                  }
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="描述下周计划完成的工作内容..."
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

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 hover:shadow-md transition-shadow">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl shadow-sm">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600 font-medium">总周报数</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{reports.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600 font-medium">平均进度</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {reports.length > 0
                  ? (
                      reports.reduce((sum, r) => sum + r.progress_percent, 0) / reports.length
                    ).toFixed(0)
                  : 0}
                %
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-orange-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600 font-medium">有风险项目</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {reports.filter((r) => r.risks && r.risks.length > 0).length}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
