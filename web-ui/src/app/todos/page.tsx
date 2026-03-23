'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiGatewayClient } from '@/lib/api/client';
import {
  Plus,
  CheckSquare,
  Clock,
  AlertCircle,
  Calendar,
  Filter,
  Search,
  Edit,
  Trash2,
  CheckCircle2,
  XCircle,
  MoreVertical,
  Flag,
} from 'lucide-react';

interface Todo {
  id: string;
  title: string;
  description?: string;
  category: string;
  priority: string;
  status: string;
  due_date?: string;
  completed_at?: string;
  project_id?: string;
  task_id?: string;
  project_name?: string;
  task_name?: string;
  user_id: string; // 分配给的用户ID
  created_by?: string; // 创建者ID（从metadata中获取）
  metadata?: any;
  created_at: string;
  updated_at: string;
}

interface TodoStatistics {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  cancelled: number;
  overdue: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
}

export default function TodosPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading, user } = useAuth();
  const [todos, setTodos] = useState<Todo[]>([]);
  const [statistics, setStatistics] = useState<TodoStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 获取当前用户ID
  const currentUserId = user?.user_id || user?.id || '';

  // 判断待办是否是自己创建的
  const isTodoCreatedByMe = (todo: Todo): boolean => {
    // 优先使用metadata中的created_by字段（最准确）
    if (todo.metadata?.created_by) {
      const isCreated = todo.metadata.created_by === currentUserId;
      console.log(
        `待办 ${todo.id} (${todo.title}): metadata.created_by=${todo.metadata.created_by}, currentUserId=${currentUserId}, isCreated=${isCreated}`
      );
      return isCreated;
    }
    // 如果没有created_by字段，且user_id等于当前用户ID，可能是自己创建的（兼容旧数据）
    // 但为了安全起见，如果没有created_by，默认认为不是自己创建的（避免误判）
    // 只有明确有created_by且匹配，才认为是自己创建的
    console.log(
      `待办 ${todo.id} (${todo.title}): 没有metadata.created_by字段，user_id=${todo.user_id}, currentUserId=${currentUserId}, 返回false（不是自己创建的）`
    );
    return false;
  };

  // 检查登录状态
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'work',
    priority: 'medium',
    due_date: '',
    project_id: '',
    task_id: '',
  });

  useEffect(() => {
    fetchTodos();
    fetchStatistics();
  }, [statusFilter, categoryFilter, priorityFilter]);

  const fetchTodos = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (categoryFilter) params.append('category', categoryFilter);
      if (priorityFilter) params.append('priority', priorityFilter);

      const query = params.toString();
      const data = await apiGatewayClient.get<{ items: Todo[] }>(
        `/api/v1/todos${query ? `?${query}` : ''}`
      );
      // 处理待办列表，从metadata中提取created_by
      const processedTodos = (data.items || []).map((todo: any) => ({
        ...todo,
        created_by: todo.metadata?.created_by || todo.user_id, // 如果没有created_by，默认使用user_id
      }));
      setTodos(processedTodos);
    } catch (error) {
      console.error('获取待办事项失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const data = await apiGatewayClient.get<TodoStatistics>('/api/v1/todos/statistics/summary');
      setStatistics(data);
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  const handleCreate = async () => {
    try {
      await apiGatewayClient.post('/api/v1/todos', {
        ...formData,
        due_date: formData.due_date || null,
        project_id: formData.project_id || null,
        task_id: formData.task_id || null,
        metadata: {
          created_by: currentUserId, // 记录创建者ID
        },
      });
      setShowCreateModal(false);
      setFormData({
        title: '',
        description: '',
        category: 'work',
        priority: 'medium',
        due_date: '',
        project_id: '',
        task_id: '',
      });
      fetchTodos();
      fetchStatistics();
    } catch (error) {
      console.error('创建待办事项失败:', error);
      alert('创建失败');
    }
  };

  const handleUpdate = async () => {
    if (!editingTodo) return;

    try {
      // 保留原有的metadata，特别是created_by
      const existingMetadata = editingTodo.metadata || {};
      await apiGatewayClient.put(`/api/v1/todos/${editingTodo.id}`, {
        ...formData,
        due_date: formData.due_date || null,
        project_id: formData.project_id || null,
        task_id: formData.task_id || null,
        metadata: {
          ...existingMetadata, // 保留原有metadata
          // created_by 保持不变
        },
      });
      setEditingTodo(null);
      setFormData({
        title: '',
        description: '',
        category: 'work',
        priority: 'medium',
        due_date: '',
        project_id: '',
        task_id: '',
      });
      fetchTodos();
      fetchStatistics();
    } catch (error) {
      console.error('更新待办事项失败:', error);
      alert('更新失败');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个待办事项吗？')) return;

    try {
      await apiGatewayClient.delete(`/api/v1/todos/${id}`);
      fetchTodos();
      fetchStatistics();
    } catch (error) {
      console.error('删除待办事项失败:', error);
      alert('删除失败');
    }
  };

  const handleComplete = async (id: string) => {
    try {
      await apiGatewayClient.patch(`/api/v1/todos/${id}/complete`);
      fetchTodos();
      fetchStatistics();
    } catch (error) {
      console.error('完成待办事项失败:', error);
      alert('完成操作失败');
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      high: 'text-red-600 bg-red-100',
      medium: 'text-yellow-600 bg-yellow-100',
      low: 'text-blue-600 bg-blue-100',
    };
    return colors[priority] || 'text-gray-600 bg-gray-100';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'text-gray-600 bg-gray-100',
      in_progress: 'text-blue-600 bg-blue-100',
      completed: 'text-green-600 bg-green-100',
      cancelled: 'text-red-600 bg-red-100',
    };
    return colors[status] || 'text-gray-600 bg-gray-100';
  };

  const getCategoryText = (category: string) => {
    const texts: Record<string, string> = {
      work: '工作',
      personal: '个人',
      urgent: '紧急',
      project: '项目',
      other: '其他',
    };
    return texts[category] || category;
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待处理',
      in_progress: '进行中',
      completed: '已完成',
      cancelled: '已取消',
    };
    return texts[status] || status;
  };

  const isOverdue = (dueDate?: string, status?: string) => {
    if (!dueDate || status === 'completed' || status === 'cancelled') return false;
    return new Date(dueDate) < new Date();
  };

  const filteredTodos = todos.filter((todo) => {
    if (
      searchQuery &&
      !todo.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !todo.description?.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div>
      {/* 操作栏 */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              setEditingTodo(null);
              setFormData({
                title: '',
                description: '',
                category: 'work',
                priority: 'medium',
                due_date: '',
                project_id: '',
                task_id: '',
              });
              setShowCreateModal(true);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="h-5 w-5" />
            新建待办
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{statistics.total}</div>
            <div className="text-sm text-gray-600">总计</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-yellow-600">{statistics.pending}</div>
            <div className="text-sm text-gray-600">待处理</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-blue-600">{statistics.in_progress}</div>
            <div className="text-sm text-gray-600">进行中</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-green-600">{statistics.completed}</div>
            <div className="text-sm text-gray-600">已完成</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-red-600">{statistics.overdue}</div>
            <div className="text-sm text-gray-600">已过期</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-red-600">{statistics.high_priority}</div>
            <div className="text-sm text-gray-600">高优先级</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-yellow-600">{statistics.medium_priority}</div>
            <div className="text-sm text-gray-600">中优先级</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-blue-600">{statistics.low_priority}</div>
            <div className="text-sm text-gray-600">低优先级</div>
          </div>
        </div>
      )}

      {/* 过滤器 */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索待办事项..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部分类</option>
            <option value="work">工作</option>
            <option value="personal">个人</option>
            <option value="urgent">紧急</option>
            <option value="project">项目</option>
            <option value="other">其他</option>
          </select>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部优先级</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
        </div>
      </div>

      {/* 待办事项列表 */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      ) : filteredTodos.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <CheckSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">暂无待办事项</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTodos.map((todo) => (
            <div
              key={todo.id}
              className={`bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow ${
                todo.status === 'completed' ? 'opacity-75' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3
                      className={`text-lg font-semibold ${todo.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'}`}
                    >
                      {todo.title}
                    </h3>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(todo.priority)}`}
                    >
                      {todo.priority === 'high' ? '高' : todo.priority === 'medium' ? '中' : '低'}
                    </span>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(todo.status)}`}
                    >
                      {getStatusText(todo.status)}
                    </span>
                    {isOverdue(todo.due_date, todo.status) && (
                      <span className="px-2 py-1 rounded text-xs font-medium text-red-600 bg-red-100 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        已过期
                      </span>
                    )}
                  </div>
                  {todo.description && <p className="text-gray-600 mb-3">{todo.description}</p>}
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {todo.due_date
                        ? new Date(todo.due_date).toLocaleDateString('zh-CN')
                        : '无截止日期'}
                    </span>
                    <span>{getCategoryText(todo.category)}</span>
                    {todo.project_name && (
                      <span className="text-blue-600">项目: {todo.project_name}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {todo.status !== 'completed' && (
                    <button
                      onClick={() => handleComplete(todo.id)}
                      className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                      title="完成"
                    >
                      <CheckCircle2 className="h-5 w-5" />
                    </button>
                  )}
                  {/* 只有自己创建的待办才显示编辑和删除按钮 */}
                  {isTodoCreatedByMe(todo) && (
                    <>
                      <button
                        onClick={() => {
                          setEditingTodo(todo);
                          setFormData({
                            title: todo.title,
                            description: todo.description || '',
                            category: todo.category,
                            priority: todo.priority,
                            due_date: todo.due_date
                              ? new Date(todo.due_date).toISOString().slice(0, 16)
                              : '',
                            project_id: todo.project_id || '',
                            task_id: todo.task_id || '',
                          });
                          setShowCreateModal(true);
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                        title="编辑"
                      >
                        <Edit className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(todo.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                        title="删除"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 创建/编辑模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  {editingTodo ? '编辑待办事项' : '新建待办事项'}
                </h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingTodo(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    标题 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入待办事项标题"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="输入待办事项描述"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">分类</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="work">工作</option>
                      <option value="personal">个人</option>
                      <option value="urgent">紧急</option>
                      <option value="project">项目</option>
                      <option value="other">其他</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">优先级</label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">低</option>
                      <option value="medium">中</option>
                      <option value="high">高</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">截止日期</label>
                  <input
                    type="datetime-local"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingTodo(null);
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={editingTodo ? handleUpdate : handleCreate}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editingTodo ? '更新' : '创建'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
