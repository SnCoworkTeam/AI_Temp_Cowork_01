'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { getUsers } from '@/lib/api/admin';
import {
  Plus,
  Building2,
  Calendar,
  Users,
  TrendingUp,
  ArrowLeft,
  Eye,
  Edit,
  Trash2,
  Search,
  Filter,
  X,
  Heart,
  DollarSign,
  Target,
  AlertCircle,
} from 'lucide-react';
import Link from 'next/link';
import ErrorMessage from '@/components/ErrorMessage';

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
  budget?: number;
  progress_percent: number;
  health_score: number;
  project_count: number;
  created_at: string;
  updated_at: string;
}

interface User {
  user_id: string;
  username: string;
  display_name?: string;
  full_name?: string;
  email?: string;
}

export default function ProgramsPage() {
  const router = useRouter();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingProgram, setEditingProgram] = useState<Program | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const pageSize = 20;

  useEffect(() => {
    fetchPrograms();
    fetchUsers();
  }, [page, statusFilter]);

  const fetchUsers = async () => {
    try {
      // 使用更小的 page_size，避免 422 错误
      const response = await getUsers({ page: 1, page_size: 100 });
      // 处理不同的响应格式
      const usersList = (response as any).users || (response as any).items || response || [];
      setUsers(Array.isArray(usersList) ? usersList : []);
    } catch (error: any) {
      console.error('获取用户列表失败:', error);
      // 不阻止页面渲染，只记录错误
      setUsers([]);
    }
  };

  const fetchPrograms = async () => {
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      let url = `${apiUrl}/api/v1/programs?skip=${(page - 1) * pageSize}&limit=${pageSize}`;
      if (statusFilter !== 'all') {
        url += `&status=${statusFilter}`;
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        let items = data.items || [];

        // 客户端搜索过滤
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          items = items.filter(
            (p: Program) =>
              p.name.toLowerCase().includes(query) ||
              p.program_code.toLowerCase().includes(query) ||
              (p.description && p.description.toLowerCase().includes(query)) ||
              (p.manager_name && p.manager_name.toLowerCase().includes(query))
          );
        }

        setPrograms(items);
        setTotal(data.total || 0);
      } else {
        setError('加载项目群列表失败');
      }
    } catch (error) {
      console.error('获取项目群列表失败:', error);
      setError('加载项目群列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (programId: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/programs/${programId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setSuccess('项目群删除成功');
        setShowDeleteConfirm(null);
        fetchPrograms();
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '删除失败' }));
        setError(errorData.detail || '删除项目群失败');
      }
    } catch (error) {
      console.error('删除项目群失败:', error);
      setError('删除项目群失败，请稍后重试');
    }
  };

  const handleEdit = (program: Program) => {
    setEditingProgram(program);
    setShowEditModal(true);
  };

  const handleSaveEdit = async (formData: any) => {
    if (!editingProgram) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/programs/${editingProgram.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSuccess('项目群更新成功');
        setShowEditModal(false);
        setEditingProgram(null);
        fetchPrograms();
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '更新失败' }));
        setError(errorData.detail || '更新项目群失败');
      }
    } catch (error) {
      console.error('更新项目群失败:', error);
      setError('更新项目群失败，请稍后重试');
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
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredPrograms = programs.filter((program) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      program.name.toLowerCase().includes(query) ||
      program.program_code.toLowerCase().includes(query) ||
      (program.description && program.description.toLowerCase().includes(query)) ||
      (program.manager_name && program.manager_name.toLowerCase().includes(query))
    );
  });

  if (loading && programs.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* 错误和成功提示 */}
      {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} autoClose />}
      {success && <ErrorMessage message={success} type="success" onClose={() => setSuccess(null)} autoClose />}

      {/* 头部 */}
      <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-lg border-2 border-indigo-200 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-white/80 rounded-lg transition-all shadow-sm hover:shadow-md"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>返回</span>
            </button>
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-500 rounded-xl shadow-lg">
                <Building2 className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">项目群管理</h1>
                <p className="text-gray-600 mt-1">管理和查看所有项目群</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => router.push('/projects/programs/create')}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl font-semibold"
          >
            <Plus className="w-5 h-5" />
            <span>创建项目群</span>
          </button>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="搜索项目群名称、编码、描述或经理..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="all">全部状态</option>
              <option value="planning">规划中</option>
              <option value="active">进行中</option>
              <option value="delayed">已延迟</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>
        </div>
      </div>

      {/* 项目群列表 */}
      {filteredPrograms.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-12 text-center">
          <Building2 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500 text-lg mb-4">
            {searchQuery || statusFilter !== 'all' ? '没有找到匹配的项目群' : '暂无项目群'}
          </p>
          {!searchQuery && statusFilter === 'all' && (
            <button
              onClick={() => router.push('/projects/programs/create')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              <span>创建第一个项目群</span>
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPrograms.map((program) => (
              <div
                key={program.id}
                className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg border-2 border-gray-200 hover:border-indigo-300 hover:shadow-2xl transition-all duration-300 overflow-hidden"
              >
                {/* 卡片头部 */}
                <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-4 text-white">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold mb-1 line-clamp-1">{program.name}</h3>
                      <p className="text-xs text-indigo-100 font-mono">{program.program_code}</p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold border-2 ${getStatusColor(program.status)}`}
                    >
                      {getStatusText(program.status)}
                    </span>
                  </div>
                </div>

                {/* 卡片内容 */}
                <div className="p-5 space-y-3">
                  {program.description && (
                    <p className="text-sm text-gray-600 line-clamp-2">{program.description}</p>
                  )}

                  <div className="space-y-2">
                    {program.manager_name && (
                      <div className="flex items-center gap-2 text-sm text-gray-700">
                        <div className="p-1.5 bg-blue-100 rounded-lg">
                          <Users className="w-4 h-4 text-blue-600" />
                        </div>
                        <span className="font-medium">经理: {program.manager_name}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm text-gray-700">
                      <div className="p-1.5 bg-purple-100 rounded-lg">
                        <Building2 className="w-4 h-4 text-purple-600" />
                      </div>
                      <span className="font-medium">项目数: {program.project_count}</span>
                    </div>
                    {program.start_date && program.end_date && (
                      <div className="flex items-center gap-2 text-sm text-gray-700">
                        <div className="p-1.5 bg-green-100 rounded-lg">
                          <Calendar className="w-4 h-4 text-green-600" />
                        </div>
                        <span>
                          {new Date(program.start_date).toLocaleDateString()} -{' '}
                          {new Date(program.end_date).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm text-gray-700">
                      <div className="p-1.5 bg-orange-100 rounded-lg">
                        <TrendingUp className="w-4 h-4 text-orange-600" />
                      </div>
                      <span className="font-medium">进度: {program.progress_percent.toFixed(1)}%</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-2 ml-2">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all"
                          style={{ width: `${program.progress_percent}%` }}
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-700">
                      <div className="p-1.5 bg-red-100 rounded-lg">
                        <Heart className={`w-4 h-4 ${getHealthColor(program.health_score)}`} />
                      </div>
                      <span className="font-medium">健康度: {program.health_score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>

                {/* 卡片底部操作按钮 */}
                <div className="px-5 pb-5 pt-3 border-t border-gray-200 bg-gray-50">
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/projects/programs/${program.id}`}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                    >
                      <Eye className="w-4 h-4" />
                      <span>查看</span>
                    </Link>
                    <button
                      onClick={() => handleEdit(program)}
                      className="flex items-center justify-center gap-2 px-3 py-2 bg-yellow-50 text-yellow-600 rounded-lg hover:bg-yellow-100 transition-colors text-sm font-medium"
                    >
                      <Edit className="w-4 h-4" />
                      <span>编辑</span>
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(program.id)}
                      className="flex items-center justify-center gap-2 px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors text-sm font-medium"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>删除</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 分页 */}
          {total > pageSize && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                上一页
              </button>
              <span className="text-sm text-gray-600">
                第 {page} 页，共 {Math.ceil(total / pageSize)} 页
              </span>
              <button
                onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
                disabled={page >= Math.ceil(total / pageSize)}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}

      {/* 编辑模态框 */}
      {showEditModal && editingProgram && (
        <EditProgramModal
          program={editingProgram}
          users={users}
          onClose={() => {
            setShowEditModal(false);
            setEditingProgram(null);
          }}
          onSave={handleSaveEdit}
        />
      )}

      {/* 删除确认对话框 */}
      {showDeleteConfirm && (
        <DeleteConfirmModal
          programName={programs.find((p) => p.id === showDeleteConfirm)?.name || ''}
          onConfirm={() => handleDelete(showDeleteConfirm)}
          onCancel={() => setShowDeleteConfirm(null)}
        />
      )}
    </div>
  );
}

// 编辑项目群模态框组件
interface EditProgramModalProps {
  program: Program;
  users: User[];
  onClose: () => void;
  onSave: (formData: any) => void;
}

function EditProgramModal({ program, users, onClose, onSave }: EditProgramModalProps) {
  const [formData, setFormData] = useState({
    name: program.name,
    description: program.description || '',
    status: program.status,
    manager_id: program.manager_id || '',
    start_date: program.start_date ? program.start_date.split('T')[0] : '',
    end_date: program.end_date ? program.end_date.split('T')[0] : '',
    budget: program.budget || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const submitData: any = {
      name: formData.name,
      description: formData.description || null,
      status: formData.status,
      manager_id: formData.manager_id || null,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
      budget: formData.budget ? parseFloat(formData.budget.toString()) : null,
    };
    onSave(submitData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">编辑项目群</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 transition-colors p-1 rounded-lg hover:bg-white/20"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">项目群名称 *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="planning">规划中</option>
                <option value="active">进行中</option>
                <option value="delayed">已延迟</option>
                <option value="completed">已完成</option>
                <option value="cancelled">已取消</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">项目经理</label>
              <select
                value={formData.manager_id}
                onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="">请选择</option>
                {users.map((user) => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.display_name || user.full_name || user.username || user.email}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">开始日期</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">结束日期</label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">预算</label>
            <input
              type="number"
              step="0.01"
              value={formData.budget}
              onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// 删除确认对话框组件
interface DeleteConfirmModalProps {
  programName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

function DeleteConfirmModal({ programName, onConfirm, onCancel }: DeleteConfirmModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-red-100 rounded-full">
            <AlertCircle className="w-6 h-6 text-red-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">确认删除</h3>
            <p className="text-sm text-gray-600 mt-1">
              确定要删除项目群 <span className="font-semibold">{programName}</span> 吗？此操作不可恢复。
            </p>
          </div>
        </div>
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            确认删除
          </button>
        </div>
      </div>
    </div>
  );
}
