'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, AlertTriangle, Filter, X, Save, Edit, Trash2, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import ErrorMessage from '@/components/ErrorMessage';

interface Risk {
  id: string;
  project_id: string;
  project_name: string;
  title: string;
  name: string;
  description: string;
  severity: string;
  risk_level: string;
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
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [expandedRisks, setExpandedRisks] = useState<Set<string>>(new Set());
  const [editingRisk, setEditingRisk] = useState<Risk | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    project_id: projectId || '',
    name: '',
    description: '',
    risk_level: 'medium',
    status: 'open',
    mitigation_plan: '',
    identified_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchProjects();
    fetchRisks();
  }, [selectedProject, severityFilter, statusFilter]);

  const fetchProjects = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      const response = await fetch(`${apiUrl}/api/v1/projects?limit=1000`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        const items = data.items || data || [];
        setProjects(Array.isArray(items) ? items : []);
      } else {
        console.error('获取项目列表失败:', response.status, response.statusText);
        setProjects([]);
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
      setProjects([]);
    }
  };

  const fetchRisks = async () => {
    try {
      setLoading(true);
      setError(null);
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
      if (response.ok) {
        const data = await response.json();
        setRisks(data.items || []);
      } else {
        const errorText = await response.text().catch(() => '获取风险列表失败');
        console.error('获取风险列表失败:', response.status, errorText);
        setError(`获取风险列表失败: ${response.status === 500 ? '服务器错误' : '请求失败'}`);
        setRisks([]);
      }
    } catch (error: any) {
      console.error('获取风险列表失败:', error);
      setError('获取风险列表失败，请稍后重试');
      setRisks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRisk = async () => {
    if (!formData.project_id) {
      setError('请选择项目');
      return;
    }
    if (!formData.name.trim()) {
      setError('请输入风险名称');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/risks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          project_id: formData.project_id,
          name: formData.name,
          description: formData.description || null,
          risk_level: formData.risk_level,
          status: formData.status,
          mitigation_plan: formData.mitigation_plan || null,
          identified_date: formData.identified_date || null,
        }),
      });

      if (response.ok) {
        setSuccess('风险创建成功');
        setShowCreateModal(false);
        resetForm();
        await fetchRisks();
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '创建风险失败' }));
        setError(errorData.detail || '创建风险失败');
      }
    } catch (error: any) {
      console.error('创建风险失败:', error);
      setError(error?.message || '创建风险失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditRisk = (risk: Risk) => {
    setEditingRisk(risk);
    setFormData({
      project_id: risk.project_id,
      name: risk.name || risk.title || '',
      description: risk.description || '',
      risk_level: risk.risk_level || risk.severity || 'medium',
      status: risk.status || 'open',
      mitigation_plan: risk.mitigation_plan || '',
      identified_date: risk.identified_date
        ? new Date(risk.identified_date).toISOString().split('T')[0]
        : new Date().toISOString().split('T')[0],
    });
    setShowEditModal(true);
  };

  const handleUpdateRisk = async () => {
    if (!editingRisk) return;
    if (!formData.name.trim()) {
      setError('请输入风险名称');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/risks/${editingRisk.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description || null,
          risk_level: formData.risk_level,
          status: formData.status,
          mitigation_plan: formData.mitigation_plan || null,
          identified_date: formData.identified_date || null,
        }),
      });

      if (response.ok) {
        setSuccess('风险更新成功');
        setShowEditModal(false);
        setEditingRisk(null);
        resetForm();
        await fetchRisks();
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '更新风险失败' }));
        setError(errorData.detail || '更新风险失败');
      }
    } catch (error: any) {
      console.error('更新风险失败:', error);
      setError(error?.message || '更新风险失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteRisk = async (riskId: string) => {
    try {
      setSubmitting(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/risks/${riskId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setSuccess('风险删除成功');
        setShowDeleteConfirm(null);
        await fetchRisks();
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '删除风险失败' }));
        setError(errorData.detail || '删除风险失败');
      }
    } catch (error: any) {
      console.error('删除风险失败:', error);
      setError(error?.message || '删除风险失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      project_id: projectId || '',
      name: '',
      description: '',
      risk_level: 'medium',
      status: 'open',
      mitigation_plan: '',
      identified_date: new Date().toISOString().split('T')[0],
    });
  };

  const toggleExpand = (riskId: string) => {
    setExpandedRisks((prev) => {
      const next = new Set(prev);
      if (next.has(riskId)) {
        next.delete(riskId);
      } else {
        next.add(riskId);
      }
      return next;
    });
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

  const renderRiskModal = (isEdit: boolean) => {
    const title = isEdit ? '编辑风险' : '新增风险';
    const handleSubmit = isEdit ? handleUpdateRisk : handleCreateRisk;
    const isOpen = isEdit ? showEditModal : showCreateModal;
    const handleClose = () => {
      if (isEdit) {
        setShowEditModal(false);
        setEditingRisk(null);
      } else {
        setShowCreateModal(false);
      }
      setError(null);
      resetForm();
    };

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
          <div className="bg-gradient-to-r from-red-50 to-orange-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">{title}</h2>
            </div>
            <button onClick={handleClose} className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
              <X className="w-5 h-5 text-gray-600" />
            </button>
          </div>

          <div className="p-6 space-y-4">
            {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}
            {success && <ErrorMessage message={success} type="success" onClose={() => setSuccess(null)} />}

            {!isEdit && (
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  项目 <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  required
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
                >
                  <option value="">请选择项目</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                风险名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
                placeholder="请输入风险名称"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">风险描述</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all resize-none"
                placeholder="请输入风险描述"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">风险等级</label>
                <select
                  value={formData.risk_level}
                  onChange={(e) => setFormData({ ...formData, risk_level: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
                >
                  <option value="low">低</option>
                  <option value="medium">中</option>
                  <option value="high">高</option>
                  <option value="critical">严重</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">状态</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
                >
                  <option value="open">待处理</option>
                  <option value="monitoring">监控中</option>
                  <option value="mitigated">已缓解</option>
                  <option value="closed">已关闭</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">识别日期</label>
              <input
                type="date"
                value={formData.identified_date}
                onChange={(e) => setFormData({ ...formData, identified_date: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">缓解措施</label>
              <textarea
                value={formData.mitigation_plan}
                onChange={(e) => setFormData({ ...formData, mitigation_plan: e.target.value })}
                rows={4}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all resize-none"
                placeholder="请输入缓解措施"
              />
            </div>
          </div>

          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
            <button
              onClick={handleClose}
              className="px-6 py-3 text-gray-700 bg-white border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-all font-semibold"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 transition-all shadow-lg hover:shadow-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>{isEdit ? '更新中...' : '创建中...'}</span>
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  <span>{isEdit ? '更新风险' : '创建风险'}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="bg-gradient-to-r from-red-50 via-orange-50 to-yellow-50 rounded-2xl shadow-xl border-2 border-red-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">风险管理</h1>
            <p className="text-sm text-gray-600 mt-1">项目风险识别、跟踪和管理</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 transition-all duration-200 flex items-center gap-2 font-semibold shadow-lg hover:shadow-xl"
          >
            <Plus className="h-5 w-5" />
            新增风险
          </button>
        </div>
      </div>

      {/* 错误和成功提示 */}
      {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} autoClose />}
      {success && <ErrorMessage message={success} type="success" onClose={() => setSuccess(null)} autoClose />}

      {/* 筛选条件 */}
      <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-5">
        <div className="flex items-center gap-2 text-gray-700 font-semibold mb-4">
          <div className="p-1.5 bg-red-100 rounded-lg">
            <Filter className="w-4 h-4 text-red-600" />
          </div>
          <span>筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 bg-white text-sm"
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
            className="px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 bg-white text-sm"
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
            className="px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有状态</option>
            <option value="open">待处理</option>
            <option value="monitoring">监控中</option>
            <option value="mitigated">已缓解</option>
            <option value="closed">已关闭</option>
          </select>
        </div>
      </div>

      {/* 风险列表 */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : risks.length === 0 ? (
        <div className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-red-100 to-orange-100 mb-4">
            <AlertTriangle className="h-10 w-10 text-red-500" />
          </div>
          <p className="text-gray-600 font-semibold text-lg mb-2">暂无风险</p>
          <p className="text-sm text-gray-500 mb-6">开始添加您的第一个风险</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 transition-all font-semibold shadow-lg hover:shadow-xl"
          >
            <Plus className="h-5 w-5" />
            添加第一个风险
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {risks.map((r) => {
            const isExpanded = expandedRisks.has(r.id);
            return (
              <div
                key={r.id}
                className="bg-white rounded-xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl hover:border-red-300 transition-all duration-200"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-gradient-to-br from-orange-100 to-orange-200 rounded-xl shadow-md flex-shrink-0">
                    <AlertTriangle className="w-7 h-7 text-orange-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-3 gap-2">
                      <h3 className="text-xl font-bold text-gray-900 truncate">{r.title || r.name}</h3>
                      <div className="flex gap-2 flex-shrink-0">
                        <span
                          className={`px-3 py-1.5 text-xs font-bold rounded-full border-2 shadow-sm ${getSeverityColor(r.severity || r.risk_level)}`}
                        >
                          {getSeverityText(r.severity || r.risk_level)}
                        </span>
                        <span
                          className={`px-3 py-1.5 text-xs font-bold rounded-full shadow-sm ${getStatusColor(r.status)}`}
                        >
                          {getStatusText(r.status)}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-700">项目:</span>
                        <span className="text-gray-600">{r.project_name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-700">识别日期:</span>
                        <span className="text-gray-600">
                          {r.identified_date
                            ? new Date(r.identified_date).toLocaleDateString('zh-CN')
                            : r.created_at
                              ? new Date(r.created_at).toLocaleDateString('zh-CN')
                              : '-'}
                        </span>
                      </div>
                    </div>

                    {r.description && (
                      <p className="text-sm text-gray-600 mb-4 line-clamp-2">{r.description}</p>
                    )}

                    {/* 展开/收起按钮 */}
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                      <button
                        onClick={() => toggleExpand(r.id)}
                        className="flex items-center gap-2 text-sm text-gray-600 hover:text-red-600 transition-colors"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="w-4 h-4" />
                            <span>收起详情</span>
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-4 h-4" />
                            <span>查看详情</span>
                          </>
                        )}
                      </button>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEditRisk(r)}
                          className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
                          title="编辑"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(r.id)}
                          className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                          title="删除"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* 展开的详情 */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                        {r.description && (
                          <div>
                            <div className="text-sm font-semibold text-gray-700 mb-2">风险描述</div>
                            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{r.description}</p>
                          </div>
                        )}
                        {r.mitigation_plan && (
                          <div>
                            <div className="text-sm font-semibold text-gray-700 mb-2">缓解措施</div>
                            <p className="text-sm text-gray-600 bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg border border-green-200">
                              {r.mitigation_plan}
                            </p>
                          </div>
                        )}
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="font-semibold text-gray-700">风险ID:</span>
                            <span className="text-gray-600 ml-2 font-mono text-xs">{r.id}</span>
                          </div>
                          <div>
                            <span className="font-semibold text-gray-700">创建时间:</span>
                            <span className="text-gray-600 ml-2">
                              {r.created_at ? new Date(r.created_at).toLocaleString('zh-CN') : '-'}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl shadow-lg border-2 border-gray-200 p-5 hover:shadow-xl transition-shadow">
          <div className="text-sm text-gray-600 font-semibold">总风险数</div>
          <div className="text-4xl font-bold text-gray-900 mt-2">{risks.length}</div>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl shadow-lg border-2 border-red-200 p-5 hover:shadow-xl transition-shadow">
          <div className="text-sm text-gray-600 font-semibold">待处理</div>
          <div className="text-4xl font-bold text-red-600 mt-2">
            {risks.filter((r) => r.status === 'open').length}
          </div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl shadow-lg border-2 border-yellow-200 p-5 hover:shadow-xl transition-shadow">
          <div className="text-sm text-gray-600 font-semibold">监控中</div>
          <div className="text-4xl font-bold text-yellow-600 mt-2">
            {risks.filter((r) => r.status === 'monitoring').length}
          </div>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl shadow-lg border-2 border-orange-200 p-5 hover:shadow-xl transition-shadow">
          <div className="text-sm text-gray-600 font-semibold">高危风险</div>
          <div className="text-4xl font-bold text-orange-600 mt-2">
            {risks.filter((r) => (r.severity || r.risk_level) === 'high' || (r.severity || r.risk_level) === 'critical')
              .length}
          </div>
        </div>
      </div>

      {/* 创建风险模态框 */}
      {renderRiskModal(false)}

      {/* 编辑风险模态框 */}
      {renderRiskModal(true)}

      {/* 删除确认对话框 */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md m-4">
            <div className="bg-gradient-to-r from-red-50 to-orange-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-500 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">确认删除</h2>
              </div>
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            <div className="p-6">
              <p className="text-gray-700 mb-4">
                确定要删除这个风险吗？此操作无法撤销。
              </p>
              {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}
            </div>

            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-6 py-3 text-gray-700 bg-white border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-all font-semibold"
              >
                取消
              </button>
              <button
                onClick={() => handleDeleteRisk(showDeleteConfirm)}
                disabled={submitting}
                className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 transition-all shadow-lg hover:shadow-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>删除中...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-5 h-5" />
                    <span>确认删除</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
