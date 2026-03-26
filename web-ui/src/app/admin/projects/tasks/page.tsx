'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, Search, CheckCircle, Clock, AlertCircle, Filter } from 'lucide-react';

interface Task {
  id: string;
  project_id: string;
  project_name: string;
  name: string;
  description: string;
  status: string;
  priority: string;
  assigned_to: string;
  start_date: string;
  due_date: string;
  progress_percent: number;
  created_at: string;
}

interface Project {
  id: string;
  name: string;
  project_code: string;
}

export default function TasksManagementPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('project_id');

  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');

  useEffect(() => {
    fetchProjects();
    fetchTasks();
  }, [selectedProject]);

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

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      let url = `${apiUrl}/api/v1/tasks`;
      if (selectedProject && selectedProject !== 'all') {
        url += `?project_id=${selectedProject}`;
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTasks(data.items || []);
      }
    } catch (error) {
      console.error('获取任务列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-700 border-gray-300',
      in_progress: 'bg-blue-100 text-blue-700 border-blue-300',
      completed: 'bg-green-100 text-green-700 border-green-300',
      blocked: 'bg-red-100 text-red-700 border-red-300',
      cancelled: 'bg-gray-100 text-gray-500 border-gray-200',
    };
    return colors[status] || colors.pending;
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待处理',
      in_progress: '进行中',
      completed: '已完成',
      blocked: '已阻塞',
      cancelled: '已取消',
    };
    return texts[status] || status;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      case 'in_progress':
        return <Clock className="w-4 h-4" />;
      case 'blocked':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
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

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
    const matchesPriority = priorityFilter === 'all' || task.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  return (
    <div className="space-y-6">
      {/* 标题和操作按钮 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5 hover:shadow-md transition-shadow">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">任务管理</h1>
          <p className="text-sm text-gray-600 font-medium mt-2">管理项目任务和进度跟踪</p>
        </div>
        <button className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-md hover:shadow-lg flex items-center gap-2">
          <Plus className="h-4 w-4" />
          新建任务
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

        <div className="grid grid-cols-1 md:grid-cols-4 gap-5 hover:shadow-md transition-shadow">
          {/* 搜索 */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="搜索任务..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

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

          {/* 状态过滤 */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有状态</option>
            <option value="pending">待处理</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
            <option value="blocked">已阻塞</option>
            <option value="cancelled">已取消</option>
          </select>

          {/* 优先级过滤 */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm"
          >
            <option value="all">所有优先级</option>
            <option value="low">低</option>
            <option value="medium">中</option>
            <option value="high">高</option>
            <option value="critical">紧急</option>
          </select>
        </div>
      </div>

      {/* 任务列表 */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500 mb-4">暂无任务</p>
          <button className="inline-block px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-md hover:shadow-lg">
            创建第一个任务
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all duration-200 transition-shadow cursor-pointer"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 hover:shadow-md transition-shadow">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h3 className="text-lg font-semibold text-gray-900">{task.name}</h3>
                    <span
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full shadow-sm border flex items-center gap-1 ${getStatusColor(task.status)}`}
                    >
                      {getStatusIcon(task.status)}
                      {getStatusText(task.status)}
                    </span>
                    <span
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full shadow-sm ${getPriorityColor(task.priority)}`}
                    >
                      {getPriorityText(task.priority)}
                    </span>
                  </div>

                  {task.description && (
                    <p className="text-sm text-gray-600 font-medium line-clamp-2">
                      {task.description}
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-5 hover:shadow-md transition-shadow text-sm text-gray-500">
                    {task.project_name && <span>项目: {task.project_name}</span>}
                    {task.assigned_to && <span>负责人: {task.assigned_to}</span>}
                    {task.due_date && (
                      <span>截止: {new Date(task.due_date).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2 min-w-[120px]">
                  <div className="text-sm text-gray-600 font-medium">进度</div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-blue-600 h-2.5 rounded-full transition-all duration-500 shadow-sm transition-all"
                      style={{ width: `${task.progress_percent}%` }}
                    />
                  </div>
                  <div className="text-sm font-medium text-gray-900">
                    {task.progress_percent.toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 统计信息 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-5 hover:shadow-md transition-shadow">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">总任务数</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{tasks.length}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">待处理</div>
          <div className="text-3xl font-bold text-gray-500 mt-2">
            {tasks.filter((t) => t.status === 'pending').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">进行中</div>
          <div className="text-3xl font-bold text-blue-600 mt-2">
            {tasks.filter((t) => t.status === 'in_progress').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">已完成</div>
          <div className="text-3xl font-bold text-green-600 mt-2">
            {tasks.filter((t) => t.status === 'completed').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
          <div className="text-sm text-gray-600 font-medium">已阻塞</div>
          <div className="text-3xl font-bold text-red-600 mt-2">
            {tasks.filter((t) => t.status === 'blocked').length}
          </div>
        </div>
      </div>
    </div>
  );
}
