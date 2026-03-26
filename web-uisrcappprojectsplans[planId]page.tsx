'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import {
  ArrowLeft,
  Calendar,
  TrendingUp,
  Settings,
  GanttChart as GanttIcon,
  History,
  AlertCircle,
  Upload,
  Download,
  X,
} from 'lucide-react';
import Link from 'next/link';
import GanttChart from '@/components/GanttChart';
import PlanTreeView from '@/components/ProjectPlans/PlanTreeView';
import TaskNodeEditor, { type TaskFormData } from '@/components/ProjectPlans/TaskNodeEditor';
import type { PlanTreeNode } from '@/types/project';

interface PlanTask {
  id: string;
  name: string;
  start: string;
  end: string;
  progress: number;
  dependencies?: string;
  is_critical?: boolean;
}

interface ProjectPlan {
  id: string;
  name: string;
  description?: string;
  version: string;
  is_active: boolean;
  is_baseline: boolean;
  start_date?: string;
  end_date?: string;
  task_count: number;
}

interface CriticalPath {
  critical_path: string[];
  critical_tasks: Record<string, any>;
  project_duration: number;
  early_start?: string;
  late_finish?: string;
}

function ProjectPlanDetailPageContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = (params?.projectId as string) || (params?.id as string);
  const planId = (params?.planId as string) || (params?.planId as string);

  const [plan, setPlan] = useState<ProjectPlan | null>(null);
  const [tasks, setTasks] = useState<PlanTask[]>([]);
  const [criticalPath, setCriticalPath] = useState<CriticalPath | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'gantt' | 'tasks' | 'tree' | 'critical' | 'history'>('gantt');
  const [changeLogs, setChangeLogs] = useState<any[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [planTree, setPlanTree] = useState<PlanTreeNode[]>([]);
  const [loadingTree, setLoadingTree] = useState(false);
  const [showTaskEditor, setShowTaskEditor] = useState(false);
  const [taskEditorMode, setTaskEditorMode] = useState<'create' | 'edit'>('create');
  const [selectedPhaseId, setSelectedPhaseId] = useState<string | undefined>();
  const [selectedTask, setSelectedTask] = useState<PlanTreeNode | null>(null);

  const fetchChangeLogs = useCallback(async () => {
    try {
      setLoadingLogs(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/change-logs?limit=100`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setChangeLogs(data.items || []);
      }
    } catch (error) {
      console.error('获取变更历史失败:', error);
    } finally {
      setLoadingLogs(false);
    }
  }, [projectId, planId]);

  const fetchPlanData = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans/${planId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPlan(data);
      } else {
        setError('加载计划失败');
      }
    } catch (error) {
      console.error('获取计划详情失败:', error);
      setError('加载计划失败');
    }
  }, [projectId, planId]);

  const fetchGanttData = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/gantt-data`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      }
    } catch (error) {
      console.error('获取甘特图数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [projectId, planId]);

  const fetchCriticalPath = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/critical-path`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCriticalPath(data);
      }
    } catch (error) {
      console.error('获取关键路径失败:', error);
    }
  }, [projectId, planId]);

  const fetchPlanTree = useCallback(async () => {
    try {
      setLoadingTree(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tree`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setPlanTree(data.tree || []);
      }
    } catch (error) {
      console.error('获取计划树形结构失败:', error);
    } finally {
      setLoadingTree(false);
    }
  }, [projectId, planId]);

  useEffect(() => {
    if (projectId && planId) {
      fetchPlanData();
      fetchGanttData();
      fetchCriticalPath();
      fetchPlanTree();
    }
  }, [projectId, planId, fetchPlanData, fetchGanttData, fetchCriticalPath, fetchPlanTree]);

  useEffect(() => {
    if (activeTab === 'history' && projectId && planId) {
      fetchChangeLogs();
    }
    if (activeTab === 'tree' && projectId && planId) {
      fetchPlanTree();
    }
  }, [activeTab, projectId, planId, fetchChangeLogs, fetchPlanTree]);

  // 检查URL参数，自动打开任务编辑器
  useEffect(() => {
    if (!searchParams) return;
    
    const action = searchParams.get('action');
    const phaseId = searchParams.get('phaseId');
    const taskId = searchParams.get('taskId');

    if (action === 'createTask' && phaseId && planId) {
      setSelectedPhaseId(phaseId);
      setTaskEditorMode('create');
      setSelectedTask(null);
      setShowTaskEditor(true);
      setActiveTab('tree'); // 切换到树形视图
      // 清除URL参数，避免重复触发
      const newUrl = `/projects/plans/${planId}?projectId=${projectId}`;
      router.replace(newUrl);
    } else if (action === 'editTask' && taskId && planTree.length > 0) {
      // 从树中找到任务节点
      const findTask = (nodes: PlanTreeNode[]): PlanTreeNode | null => {
        for (const node of nodes) {
          if (node.id === taskId && node.type === 'task') {
            return node;
          }
          if (node.children) {
            const found = findTask(node.children);
            if (found) return found;
          }
        }
        return null;
      };
      const task = findTask(planTree);
      if (task) {
        setSelectedTask(task);
        setTaskEditorMode('edit');
        setShowTaskEditor(true);
        setActiveTab('tree'); // 切换到树形视图
        // 清除URL参数，避免重复触发
        const newUrl = `/projects/plans/${planId}?projectId=${projectId}`;
        router.replace(newUrl);
      }
    }
  }, [searchParams, planTree, projectId, planId, router]);

  const handleTaskChange = async (taskId: string, start: Date, end: Date) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 更新任务日期
      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks/${taskId}`,
        {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            start_date: start.toISOString().split('T')[0],
            end_date: end.toISOString().split('T')[0],
          }),
        }
      );

      if (response.ok) {
        // 重新获取数据
        fetchGanttData();
        fetchCriticalPath();
      } else {
        alert('更新任务失败');
      }
    } catch (error) {
      console.error('更新任务失败:', error);
      alert('更新任务失败');
    }
  };

  const handleRecalculateSchedule = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/calculate-schedule`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCriticalPath(data);
        fetchGanttData();
        alert('计划时间表已重新计算');
      } else {
        alert('重新计算失败');
      }
    } catch (error) {
      console.error('重新计算失败:', error);
      alert('重新计算失败');
    }
  };

  const handleExportPlan = async (format: string = 'excel') => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/export?format=${format}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `plan_${plan?.name || 'export'}_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : format === 'msp' ? 'xml' : 'json'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('导出失败');
      }
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败');
    }
  };

  const handleImportPlan = async () => {
    if (!importFile) {
      alert('请选择文件');
      return;
    }

    try {
      setImporting(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const formData = new FormData();
      formData.append('file', importFile);
      formData.append('plan_name', plan?.name || '导入的计划');

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans/import`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        alert(
          `导入成功！创建了 ${data.tasks_created} 个任务${data.tasks_failed > 0 ? `，${data.tasks_failed} 个任务失败` : ''}`
        );
        setShowImportModal(false);
        setImportFile(null);
        // 刷新数据
        fetchPlanData();
        fetchGanttData();
        fetchCriticalPath();
      } else {
        const errorData = await response.json();
        alert(errorData.detail || '导入失败');
      }
    } catch (error) {
      console.error('导入失败:', error);
      alert('导入失败');
    } finally {
      setImporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
          <p className="font-semibold mb-2">{error || '计划不存在'}</p>
          <Link href={`/projects/${projectId}`} className="text-blue-600 hover:underline">
            返回项目详情
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>返回</span>
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{plan.name}</h1>
            {plan.description && <p className="text-gray-600 mt-1">{plan.description}</p>}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleExportPlan('excel')}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>导出</span>
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>导入</span>
          </button>
          <button
            onClick={handleRecalculateSchedule}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>重新计算</span>
          </button>
        </div>
      </div>

      {/* 计划信息卡片 */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl shadow-lg border-2 border-blue-200 p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">版本</p>
            <p className="text-lg font-semibold text-gray-900">{plan.version}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">任务数量</p>
            <p className="text-lg font-semibold text-gray-900">{plan.task_count}</p>
          </div>
          {criticalPath && (
            <>
              <div>
                <p className="text-sm text-gray-600 mb-1">项目工期</p>
                <p className="text-lg font-semibold text-gray-900">
                  {criticalPath.project_duration} 天
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">关键任务</p>
                <p className="text-lg font-semibold text-red-600">
                  {Object.keys(criticalPath.critical_tasks).length} 个
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('gantt')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'gantt'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <GanttIcon className="w-4 h-4" />
              <span>甘特图</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('tree')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tree'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span>树形结构</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('critical')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'critical'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              <span>关键路径</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <History className="w-4 h-4" />
              <span>变更历史</span>
            </div>
          </button>
        </nav>
      </div>

      {/* 内容区域 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
        {activeTab === 'gantt' && (
          <div>
            {tasks.length > 0 ? (
              <GanttChart
                tasks={tasks}
                onTaskChange={handleTaskChange}
                onTaskClick={(taskId) => {
                  console.log('Task clicked:', taskId);
                }}
                viewMode="Month"
                height={600}
              />
            ) : (
              <div className="text-center py-12 text-gray-500">
                <GanttIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>暂无任务数据</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'tree' && (
          <div>
            <PlanTreeView
              tree={planTree}
              loading={loadingTree}
              onAddTask={(phaseId) => {
                setSelectedPhaseId(phaseId);
                setTaskEditorMode('create');
                setSelectedTask(null);
                setShowTaskEditor(true);
              }}
              onEditTask={(taskId) => {
                // 从树中找到任务节点
                const findTask = (nodes: PlanTreeNode[]): PlanTreeNode | null => {
                  for (const node of nodes) {
                    if (node.id === taskId && node.type === 'task') {
                      return node;
                    }
                    if (node.children) {
                      const found = findTask(node.children);
                      if (found) return found;
                    }
                  }
                  return null;
                };
                const task = findTask(planTree);
                if (task) {
                  setSelectedTask(task);
                  setTaskEditorMode('edit');
                  setShowTaskEditor(true);
                }
              }}
              onDeleteTask={async (taskId) => {
                if (confirm('确定要删除此任务吗？')) {
                  try {
                    const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
                    const token = getAccessToken();

                    const response = await fetch(
                      `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks/${taskId}`,
                      {
                        method: 'DELETE',
                        headers: {
                          Authorization: `Bearer ${token}`,
                        },
                      }
                    );

                    if (response.ok) {
                      alert('任务删除成功');
                      fetchPlanTree();
                      fetchGanttData();
                      fetchCriticalPath();
                    } else {
                      alert('任务删除失败');
                    }
                  } catch (error) {
                    console.error('删除任务失败:', error);
                    alert('删除任务失败');
                  }
                }
              }}
            />
          </div>
        )}

        {activeTab === 'critical' && criticalPath && (
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-semibold text-yellow-800 mb-2">关键路径信息</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-yellow-700">项目工期：</span>
                  <span className="font-semibold">{criticalPath.project_duration} 天</span>
                </div>
                <div>
                  <span className="text-yellow-700">关键任务数：</span>
                  <span className="font-semibold">
                    {Object.keys(criticalPath.critical_tasks).length} 个
                  </span>
                </div>
                {criticalPath.early_start && (
                  <div>
                    <span className="text-yellow-700">最早开始：</span>
                    <span className="font-semibold">{criticalPath.early_start}</span>
                  </div>
                )}
                {criticalPath.late_finish && (
                  <div>
                    <span className="text-yellow-700">最晚结束：</span>
                    <span className="font-semibold">{criticalPath.late_finish}</span>
                  </div>
                )}
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-3">关键任务列表</h3>
              <div className="space-y-2">
                {Object.entries(criticalPath.critical_tasks).map(
                  ([taskId, taskInfo]: [string, any]) => (
                    <div
                      key={taskId}
                      className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between"
                    >
                      <div>
                        <p className="font-semibold text-red-900">{taskInfo.name}</p>
                        <div className="flex items-center gap-4 mt-1 text-sm text-red-700">
                          {taskInfo.early_start && <span>ES: {taskInfo.early_start}</span>}
                          {taskInfo.early_finish && <span>EF: {taskInfo.early_finish}</span>}
                          {taskInfo.total_float !== undefined && (
                            <span>浮动: {taskInfo.total_float} 天</span>
                          )}
                        </div>
                      </div>
                      <span className="px-3 py-1 bg-red-600 text-white rounded-full text-xs font-medium">
                        关键任务
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-4">
            {loadingLogs ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
                <p className="text-gray-600">加载变更历史中...</p>
              </div>
            ) : changeLogs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <History className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>暂无变更历史</p>
              </div>
            ) : (
              <div className="space-y-4">
                {changeLogs.map((log) => (
                  <div
                    key={log.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div
                          className={`p-2 rounded-lg ${
                            log.critical_path_changed
                              ? 'bg-red-100 text-red-600'
                              : 'bg-blue-100 text-blue-600'
                          }`}
                        >
                          {log.critical_path_changed ? (
                            <AlertCircle className="w-5 h-5" />
                          ) : (
                            <History className="w-5 h-5" />
                          )}
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900">
                            {log.change_type === 'task_added' && '添加任务'}
                            {log.change_type === 'task_updated' && '更新任务'}
                            {log.change_type === 'task_deleted' && '删除任务'}
                            {log.change_type === 'dependency_changed' && '变更依赖'}
                            {log.change_type === 'date_updated' && '更新日期'}
                            {log.change_type === 'plan_updated' && '更新计划'}
                            {![
                              'task_added',
                              'task_updated',
                              'task_deleted',
                              'dependency_changed',
                              'date_updated',
                              'plan_updated',
                            ].includes(log.change_type) && log.change_type}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {log.timestamp && new Date(log.timestamp).toLocaleString('zh-CN')}
                          </p>
                        </div>
                      </div>
                      {log.critical_path_changed && (
                        <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                          关键路径变更
                        </span>
                      )}
                    </div>

                    {log.change_details && Object.keys(log.change_details).length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-sm font-medium text-gray-700 mb-2">变更详情：</p>
                        <div className="bg-gray-50 rounded-lg p-3 text-sm">
                          <pre className="whitespace-pre-wrap text-gray-700">
                            {JSON.stringify(log.change_details, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}

                    {log.before_snapshot && log.after_snapshot && (
                      <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">变更前：</p>
                          <div className="bg-red-50 rounded-lg p-3 text-sm max-h-48 overflow-y-auto">
                            <pre className="whitespace-pre-wrap text-red-700 text-xs">
                              {JSON.stringify(log.before_snapshot, null, 2)}
                            </pre>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">变更后：</p>
                          <div className="bg-green-50 rounded-lg p-3 text-sm max-h-48 overflow-y-auto">
                            <pre className="whitespace-pre-wrap text-green-700 text-xs">
                              {JSON.stringify(log.after_snapshot, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 导入模态框 */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">导入项目计划</h2>
              <button
                onClick={() => {
                  setShowImportModal(false);
                  setImportFile(null);
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    选择Excel文件
                  </label>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setImportFile(file);
                      }
                    }}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  />
                  <p className="text-xs text-gray-500 mt-1">支持 .xlsx 和 .xls 格式的Excel文件</p>
                </div>

                {importFile && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">已选择文件：</span>
                      {importFile.name}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      文件大小: {(importFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                )}
              </div>
            </div>
            <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowImportModal(false);
                  setImportFile(null);
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleImportPlan}
                disabled={!importFile || importing}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {importing ? '导入中...' : '导入'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 任务编辑器模态框 */}
      <TaskNodeEditor
        visible={showTaskEditor}
        mode={taskEditorMode}
        phaseId={selectedPhaseId}
        task={selectedTask || undefined}
        onSave={async (taskData) => {
          try {
            const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
            const token = getAccessToken();

            const url =
              taskEditorMode === 'create'
                ? `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks`
                : `${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tasks/${selectedTask?.id}`;

            const response = await fetch(url, {
              method: taskEditorMode === 'create' ? 'POST' : 'PUT',
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                ...taskData,
                phase_id: selectedPhaseId || selectedTask?.phase_id,
              }),
            });

            if (response.ok) {
              fetchPlanTree();
              fetchGanttData();
              fetchCriticalPath();
            } else {
              const errorData = await response.json();
              throw new Error(errorData.detail || '保存失败');
            }
          } catch (error: any) {
            throw error;
          }
        }}
        onCancel={() => {
          setShowTaskEditor(false);
          setSelectedPhaseId(undefined);
          setSelectedTask(null);
        }}
      />
    </div>
  );
}

export default function ProjectPlanDetailPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen">加载中...</div>}>
      <ProjectPlanDetailPageContent />
    </Suspense>
  );
}

