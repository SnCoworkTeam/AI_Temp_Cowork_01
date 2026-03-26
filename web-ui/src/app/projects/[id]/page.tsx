'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { apiGatewayClient } from '@/lib/api/client';
import {
  ArrowLeft,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Users,
  Clock,
  FileText,
  Edit,
  Trash2,
  X,
  Save,
  GanttChart as GanttIcon,
  Plus,
  List,
  ChevronRight,
  ChevronDown,
  Folder,
  Lock,
  Building2,
  DollarSign,
  Target,
} from 'lucide-react';
import Link from 'next/link';
import { getUsers, User } from '@/lib/api/admin';
import ProjectPhaseProgress from '@/components/ProjectPhaseProgress';
import ProjectPlansSection from '@/components/ProjectPlansSection';
import dynamic from 'next/dynamic';

// 动态导入 Ant Design 组件，避免 SSR 和 HMR 问题
const PlanTreeView = dynamic(() => import('@/components/ProjectPlans/PlanTreeView'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center p-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>,
});

const PlanTreeTable = dynamic(() => import('@/components/ProjectPlans/PlanTreeTable'), {
  ssr: false,
});

const PlanExcelTable = dynamic(() => import('@/components/ProjectPlans/PlanExcelTable'), {
  ssr: false,
});

const TaskList = dynamic(() => import('@/components/ProjectPlans/TaskList'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center p-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>,
});

const TemplateSelector = dynamic(() => import('@/components/ProjectPlans/TemplateSelector'), {
  ssr: false,
});
import { ErrorBoundary } from '@/components/ErrorBoundary';
import ErrorMessage from '@/components/ErrorMessage';
import type { PlanTreeNode } from '@/types/project';

interface BasicDataCategory {
  id: string;
  category_type: string;
  code: string;
  name: string;
  description?: string;
}

interface Project {
  id: string;
  project_code: string;
  name: string;
  description: string;
  status: string;
  priority: string;
  start_date: string;
  end_date: string;
  progress_percent: number;
  health_score: number;
  created_at: string;
  updated_at: string;
  basic_data_categories?: BasicDataCategory[];
  reporter_id?: string;
  reporter_name?: string;
  manager_id?: string;
  manager_name?: string;
  milestone_implementation_start?: string; // 实施启动日期
  milestone_solution_confirmation?: string; // 方案确认日期
  milestone_delivery_online?: string; // 交付上线日期
  milestone_project_acceptance?: string; // 项目验收日期
  requires_weekly_report?: boolean; // 是否编写周报
}

interface Task {
  id: string;
  name: string;
  status: string;
  progress_percent: number;
}

interface Milestone {
  id: string;
  name: string;
  status: string;
  target_date: string;
}

interface ProjectPlan {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  version: string;
  is_active: boolean;
  is_baseline: boolean;
  start_date?: string;
  end_date?: string;
  task_count: number;
  template_id?: string;
  created_at: string;
  updated_at: string;
}

interface ProjectPhase {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  sequence: number;
  start_date?: string;
  end_date?: string;
  progress_percent: number;
  category_id?: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  // 验证项目ID是否为有效的UUID格式，如果不是则重定向
  useEffect(() => {
    if (projectId) {
      // UUID格式验证：8-4-4-4-12 格式
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!uuidRegex.test(projectId) || projectId === 'basic-data') {
        // 如果不是有效的UUID或者是'basic-data'，重定向到项目列表
        console.error('无效的项目ID:', projectId);
        router.push('/projects');
        return;
      }
    }
  }, [projectId, router]);

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: '',
    priority: '',
    manager_id: '',
    reporter_id: '',
    start_date: '',
    end_date: '',
    budget: '',
    progress_percent: '',
    health_score: '',
    basic_data_categories: {} as Record<string, string>, // 改为对象，每个分类类型对应一个分类ID
    milestone_implementation_start: '', // 实施启动日期
    milestone_solution_confirmation: '', // 方案确认日期
    milestone_delivery_online: '', // 交付上线日期
    milestone_project_acceptance: '', // 项目验收日期
    requires_weekly_report: false, // 是否编写周报
  });
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'plans' | 'weekly-reports' | 'monthly-reports'>('overview');
  const [phases, setPhases] = useState<ProjectPhase[]>([]);
  const [plans, setPlans] = useState<ProjectPlan[]>([]);
  const [loadingPhases, setLoadingPhases] = useState(false);
  const [loadingPlans, setLoadingPlans] = useState(false);

  useEffect(() => {
    if (projectId) {
      fetchProjectData();
      loadUsers();
      loadCategories();
      fetchPhases();
    }
  }, [projectId]);

  useEffect(() => {
    if (activeTab === 'plans' && projectId) {
      fetchPhases();
      fetchPlans();
    }
    // 周报和月报的数据会在各自的组件中加载
  }, [activeTab, projectId]);

  const loadUsers = async () => {
    try {
      const response = await getUsers({ page: 1, page_size: 100 });
      const usersList = (response as any).users || (response as any).items || [];
      setUsers(usersList);
    } catch (error) {
      console.error('加载用户列表失败:', error);
    }
  };

  const loadCategories = async () => {
    try {
      setLoadingCategories(true);
      const data = await apiGatewayClient.get<{ items: any[] }>('/api/v1/basic-data/categories?limit=1000');
      setCategories(data.items || []);
    } catch (error: any) {
      console.error('加载基础数据分类失败:', error);
      // 如果是401错误，ApiClient已经处理了重定向
      if (error?.statusCode === 401) {
        return; // 静默处理，不显示错误
      }
    } finally {
      setLoadingCategories(false);
    }
  };

  const fetchPhases = async () => {
    try {
      setLoadingPhases(true);
      const data = await apiGatewayClient.get<{ items: ProjectPhase[] }>(`/api/v1/project-phases?project_id=${projectId}`);
      const sortedPhases = (data?.items || []).sort((a: ProjectPhase, b: ProjectPhase) =>
        (a.sequence || 0) - (b.sequence || 0)
      );
      setPhases(sortedPhases);
      // 如果阶段存在但没有对应的计划，自动创建计划
      if (sortedPhases.length > 0) {
        try {
          await ensurePlansForPhases(sortedPhases);
        } catch (e) {
          console.error('自动创建计划失败:', e);
          // 不阻止页面渲染，只记录错误
        }
      }
    } catch (error: any) {
      console.error('获取项目阶段失败:', error);
      // 如果是401错误，ApiClient已经处理了重定向
      if (error?.statusCode === 401) {
        return; // 静默处理，不显示错误
      }
      // 设置空数组，避免页面崩溃
      setPhases([]);
    } finally {
      setLoadingPhases(false);
    }
  };

  const fetchPlans = async () => {
    try {
      setLoadingPlans(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans?limit=100`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data.items || []);
      }
    } catch (error) {
      console.error('获取项目计划失败:', error);
    } finally {
      setLoadingPlans(false);
    }
  };

  const ensurePlansForPhases = async (phasesList: ProjectPhase[]) => {
    if (!phasesList || phasesList.length === 0) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
    const token = getAccessToken();

    // 获取现有计划
    const plansResponse = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans?limit=100`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    let existingPlans: ProjectPlan[] = [];
    if (plansResponse.ok) {
      const plansData = await plansResponse.json();
      existingPlans = plansData.items || [];
    }

    // 如果已有计划，不需要再创建
    if (existingPlans.length > 0) {
      return;
    }

    // 查找"标准信息化项目管理模板"
    try {
      const templatesResponse = await fetch(`${apiUrl}/api/v1/project-templates?is_active=true`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (templatesResponse.ok) {
        const templatesData = await templatesResponse.json();
        const templates = templatesData.items || [];

        // 查找名为"标准信息化项目管理模板"的模板
        let template = templates.find(
          (t: any) => t.name === '标准信息化项目管理模板' || t.name.includes('标准信息化')
        );

        // 如果没找到，使用第一个启用的模板
        if (!template && templates.length > 0) {
          template = templates[0];
        }

        if (template) {
          // 创建基于模板的主计划
          const planResponse = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans`, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: project?.name ? `${project.name}项目计划` : '项目计划',
              description: `基于模板"${template.name}"自动创建`,
              template_id: template.id,
            }),
          });

          if (planResponse.ok) {
            console.log(`已基于模板"${template.name}"创建项目计划`);
          } else {
            console.error('创建项目计划失败:', await planResponse.text());
          }
        } else {
          // 如果没有模板，创建一个不带模板的计划
          const planResponse = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans`, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              name: project?.name ? `${project.name}项目计划` : '项目计划',
              description: '项目计划',
            }),
          });

          if (!planResponse.ok) {
            console.error('创建项目计划失败:', await planResponse.text());
          }
        }
      }
    } catch (error) {
      console.error('获取模板或创建计划失败:', error);
    }

    // 重新获取计划列表
    await fetchPlans();
  };

  const fetchProjectData = async () => {
    try {
      setLoading(true);
      setError('');

      const data = await apiGatewayClient.get<any>(`/api/v1/projects/${projectId}`);

      if (!data) {
        setError('项目不存在');
        setLoading(false);
        return;
      }

      setProject(data);

      // 将项目名称存储到sessionStorage，供面包屑导航使用
      if (typeof window !== 'undefined' && data.name) {
        try {
          sessionStorage.setItem(`project_name_${projectId}`, data.name);
        } catch (e) {
          console.warn('无法存储项目名称到sessionStorage:', e);
        }
      }

      // 初始化表单数据
      // 将分类数组转换为对象，每个分类类型对应一个分类ID（单选）
      const categoryMap: Record<string, string> = {};
      if (data.basic_data_categories && Array.isArray(data.basic_data_categories)) {
        data.basic_data_categories.forEach((cat: any) => {
          // 如果该分类类型还没有值，则设置（只保留第一个）
          if (cat && cat.category_type && cat.id && !categoryMap[cat.category_type]) {
            categoryMap[cat.category_type] = cat.id;
          }
        });
      }

      // 安全地处理日期字符串
      const safeDateSplit = (dateStr: string | null | undefined): string => {
        if (!dateStr) return '';
        try {
          return dateStr.split('T')[0];
        } catch (e) {
          return '';
        }
      };

      setFormData({
        name: data.name || '',
        description: data.description || '',
        status: data.status || '',
        priority: data.priority || '',
        manager_id: data.manager_id || '',
        reporter_id: data.reporter_id || '',
        start_date: safeDateSplit(data.start_date),
        end_date: safeDateSplit(data.end_date),
        budget: data.budget?.toString() || '',
        progress_percent: data.progress_percent?.toString() || '',
        health_score: data.health_score?.toString() || '',
        basic_data_categories: categoryMap,
        milestone_implementation_start: safeDateSplit(data.milestone_implementation_start),
        milestone_solution_confirmation: safeDateSplit(data.milestone_solution_confirmation),
        milestone_delivery_online: safeDateSplit(data.milestone_delivery_online),
        milestone_project_acceptance: safeDateSplit(data.milestone_project_acceptance),
        requires_weekly_report: data.requires_weekly_report || false,
      });
    } catch (error: any) {
      console.error('获取项目详情失败:', error);
      // 如果是401错误，ApiClient已经处理了重定向
      if (error?.statusCode === 401) {
        return; // 静默处理，不显示错误
      }
      // 如果是404错误
      if (error?.statusCode === 404) {
        setError('项目不存在');
      } else if (error?.statusCode === 500) {
        setError('服务器错误，请稍后重试');
      } else {
        setError(error?.message || '加载项目详情失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-gray-100 text-gray-700 border-gray-300',
      active: 'bg-blue-100 text-blue-700 border-blue-300',
      delayed: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      completed: 'bg-green-100 text-green-700 border-green-300',
      cancelled: 'bg-red-100 text-red-700 border-red-300',
    };
    return colors[status] || colors.planning;
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      planning: '规划中',
      active: '进行中',
      delayed: '已延迟',
      completed: '已完成',
      cancelled: '已取消',
    };
    return texts[status] || status;
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

  const handleEdit = () => {
    if (project) {
      setShowEditModal(true);
    }
  };

  const handleSave = async (): Promise<void> => {
    if (!project) return;

    try {
      setSaving(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const updateData: any = {};
      if (formData.name) updateData.name = formData.name;
      if (formData.description !== undefined) updateData.description = formData.description;
      if (formData.status) updateData.status = formData.status;
      if (formData.priority) updateData.priority = formData.priority;
      if (formData.manager_id) updateData.manager_id = formData.manager_id;
      if (formData.reporter_id !== undefined) updateData.reporter_id = formData.reporter_id || null;
      if (formData.start_date) updateData.start_date = formData.start_date;
      if (formData.end_date) updateData.end_date = formData.end_date;
      if (formData.budget) updateData.budget = parseFloat(formData.budget);
      if (formData.progress_percent)
        updateData.progress_percent = parseFloat(formData.progress_percent);
      if (formData.health_score) updateData.health_score = parseFloat(formData.health_score);
      if (formData.milestone_implementation_start)
        updateData.milestone_implementation_start = formData.milestone_implementation_start;
      if (formData.milestone_solution_confirmation)
        updateData.milestone_solution_confirmation = formData.milestone_solution_confirmation;
      if (formData.milestone_delivery_online)
        updateData.milestone_delivery_online = formData.milestone_delivery_online;
      if (formData.milestone_project_acceptance)
        updateData.milestone_project_acceptance = formData.milestone_project_acceptance;
      if (formData.requires_weekly_report !== undefined)
        updateData.requires_weekly_report = formData.requires_weekly_report;

      // 先更新项目基本信息
      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        // 更新项目分类关联（单选模式）
        if (formData.basic_data_categories) {
          // 获取当前项目的分类关联
          const currentMappingsResponse = await fetch(
            `${apiUrl}/api/v1/basic-data/projects/${projectId}/basic-data`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          if (currentMappingsResponse.ok) {
            const currentMappings = await currentMappingsResponse.json();
            const currentMappingsByType: Record<string, any> = {};
            if (currentMappings.items) {
              currentMappings.items.forEach((m: any) => {
                currentMappingsByType[m.category_type] = m;
              });
            }

            // 处理每个分类类型
            for (const [categoryType, categoryId] of Object.entries(
              formData.basic_data_categories
            )) {
              const currentMapping = currentMappingsByType[categoryType];

              if (categoryId) {
                // 如果选择了分类
                if (currentMapping && currentMapping.category_id === categoryId) {
                  // 已经存在且相同，无需更新
                  continue;
                } else {
                  // 需要更新：先删除旧的，再添加新的
                  if (currentMapping) {
                    await fetch(
                      `${apiUrl}/api/v1/basic-data/projects/${projectId}/basic-data/${currentMapping.id}`,
                      {
                        method: 'DELETE',
                        headers: {
                          Authorization: `Bearer ${token}`,
                        },
                      }
                    );
                  }

                  // 添加新分类
                  await fetch(`${apiUrl}/api/v1/basic-data/projects/${projectId}/basic-data`, {
                    method: 'POST',
                    headers: {
                      Authorization: `Bearer ${token}`,
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ category_id: categoryId }),
                  });
                }
              } else {
                // 如果清空了分类，删除现有的
                if (currentMapping) {
                  await fetch(
                    `${apiUrl}/api/v1/basic-data/projects/${projectId}/basic-data/${currentMapping.id}`,
                    {
                      method: 'DELETE',
                      headers: {
                        Authorization: `Bearer ${token}`,
                      },
                    }
                  );
                }
              }
            }

            // 删除不再需要的分类类型（如果表单中没有该类型，但数据库中有）
            for (const mapping of currentMappings.items || []) {
              if (!formData.basic_data_categories[mapping.category_type]) {
                await fetch(
                  `${apiUrl}/api/v1/basic-data/projects/${projectId}/basic-data/${mapping.id}`,
                  {
                    method: 'DELETE',
                    headers: {
                      Authorization: `Bearer ${token}`,
                    },
                  }
                );
              }
            }
          }
        }

        // 重新加载项目数据
        await fetchProjectData();
        setShowEditModal(false);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '更新项目失败');
      }
    } catch (error) {
      console.error('更新项目失败:', error);
      setError('网络错误');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (): Promise<void> => {
    if (!project) return;

    try {
      setDeleting(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // 删除成功，跳转到项目列表
        router.push('/projects');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '删除项目失败');
        setShowDeleteConfirm(false);
      }
    } catch (error) {
      console.error('删除项目失败:', error);
      setError('网络错误');
      setShowDeleteConfirm(false);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || '项目不存在'}
        </div>
        <Link href="/projects" className="inline-block mt-4 text-blue-600 hover:underline">
          返回项目列表
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* 返回按钮和操作按钮 */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.back()}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex gap-2 items-center">
          <button
            onClick={handleEdit}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Edit className="w-4 h-4" />
            <span>编辑</span>
          </button>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>删除</span>
          </button>
        </div>
      </div>

      {/* 页签导航 - 移到项目信息上方 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'overview'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <List className="w-4 h-4" />
                <span>概览</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('plans')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'plans'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <GanttIcon className="w-4 h-4" />
                <span>项目计划</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('weekly-reports')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'weekly-reports'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <span>周报</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('monthly-reports')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'monthly-reports'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>月报</span>
              </div>
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* 段落1: 基本信息 */}
              <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-5 border-b-2 border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-500 rounded-lg">
                        <Building2 className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
                        <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                          <span>
                            项目编码:{' '}
                            <span className="font-mono font-semibold text-gray-900">
                              {project.project_code}
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <span
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border-2 shadow-sm ${getStatusColor(project.status)}`}
                      >
                        {getStatusText(project.status)}
                      </span>
                      <span
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold shadow-sm ${getPriorityColor(project.priority)}`}
                      >
                        {getPriorityText(project.priority)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="p-6 space-y-6">
                  {/* 项目描述 */}
                  {project.description && (
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">项目描述</label>
                      <div className="bg-gray-50 rounded-xl p-4 border-2 border-gray-200">
                        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{project.description}</p>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 项目状态 */}
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">项目状态</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        <span className={`px-3 py-1.5 rounded-full text-sm font-semibold border-2 shadow-sm ${getStatusColor(project.status)}`}>
                          {getStatusText(project.status)}
                        </span>
                      </div>
                    </div>

                    {/* 优先级 */}
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">优先级</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        <span className={`px-3 py-1.5 rounded-full text-sm font-semibold shadow-sm ${getPriorityColor(project.priority)}`}>
                          {getPriorityText(project.priority)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 段落2: 时间信息 */}
              <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 px-6 py-5 border-b-2 border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-500 rounded-lg">
                      <Calendar className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900">时间信息</h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {project.start_date && (
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">计划开始日期</label>
                        <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                          <p className="text-gray-900 font-semibold">{new Date(project.start_date).toLocaleDateString('zh-CN')}</p>
                        </div>
                      </div>
                    )}
                    {project.end_date && (
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">计划结束日期</label>
                        <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                          <p className="text-gray-900 font-semibold">{new Date(project.end_date).toLocaleDateString('zh-CN')}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 段落3: 人员信息 */}
              <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 px-6 py-5 border-b-2 border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500 rounded-lg">
                      <Users className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900">人员信息</h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {project.manager_name && (
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">项目经理</label>
                        <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                          <p className="text-gray-900 font-semibold">{project.manager_name}</p>
                        </div>
                      </div>
                    )}
                    {project.reporter_name && (
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">填报人</label>
                        <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                          <p className="text-gray-900 font-semibold">{project.reporter_name}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 段落4: 预算与进度 */}
              <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 px-6 py-5 border-b-2 border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-500 rounded-lg">
                      <DollarSign className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900">预算与进度</h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">进度 (%)</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        <p className="text-2xl font-bold text-orange-600">{project.progress_percent.toFixed(1)}%</p>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">健康度</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        <p className="text-2xl font-bold text-green-600">{project.health_score.toFixed(1)}</p>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">是否编写周报</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        {project.requires_weekly_report ? (
                          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                            是
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold bg-gray-100 text-gray-800">
                            否
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 段落5: 项目分类 */}
              {project.basic_data_categories &&
                project.basic_data_categories.length > 0 &&
                (() => {
                  const allowedTypes = ['project_phase', 'phase_status', 'application_domain', 'project_category'];
                  const filtered = project.basic_data_categories.filter((cat) =>
                    allowedTypes.includes(cat.category_type)
                  );
                  const grouped = filtered.reduce(
                    (acc, cat) => {
                      if (!acc[cat.category_type]) {
                        acc[cat.category_type] = [];
                      }
                      acc[cat.category_type].push(cat);
                      return acc;
                    },
                    {} as Record<string, BasicDataCategory[]>
                  );
                  const processed: Record<string, BasicDataCategory[]> = {};
                  Object.entries(grouped).forEach(([type, categories]) => {
                    if (!processed[type]) {
                      if (type === 'application_domain') {
                        const allowedCodes = ['01-', '02-', '03-', '04-', '05-', '06-', '07-', '08-', '09-', '10-', '11-', '12-', '99-'];
                        const filtered = categories.filter((cat) => {
                          if (!cat.code) return false;
                          return allowedCodes.some((code) => cat.code.startsWith(code));
                        });
                        processed[type] = filtered.sort((a, b) => {
                          const aCode = a.code || '';
                          const bCode = b.code || '';
                          return aCode.localeCompare(bCode);
                        });
                      } else {
                        processed[type] = categories.sort((a, b) => {
                          const aHasCode = a.code && /^\d{2}-/.test(a.code);
                          const bHasCode = b.code && /^\d{2}-/.test(b.code);
                          if (aHasCode && !bHasCode) return -1;
                          if (!aHasCode && bHasCode) return 1;
                          return 0;
                        });
                      }
                    }
                  });
                  const categoryTypeNames: Record<string, string> = {
                    project_phase: '项目阶段',
                    phase_status: '阶段状态',
                    application_domain: '应用领域',
                    project_category: '项目分类',
                  };
                  const categoryOrder: Record<string, number> = {
                    project_phase: 1,
                    phase_status: 2,
                    application_domain: 3,
                    project_category: 4,
                  };
                  const sortedEntries = Object.entries(processed).sort(([typeA], [typeB]) => {
                    const orderA = categoryOrder[typeA] ?? 999;
                    const orderB = categoryOrder[typeB] ?? 999;
                    return orderA - orderB;
                  });
                  if (sortedEntries.length === 0) return null;
                  return (
                    <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
                      <div className="bg-gradient-to-r from-indigo-50 via-blue-50 to-cyan-50 px-6 py-5 border-b-2 border-gray-200">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-indigo-500 rounded-lg">
                            <Target className="w-5 h-5 text-white" />
                          </div>
                          <h2 className="text-xl font-bold text-gray-900">项目分类</h2>
                        </div>
                      </div>
                      <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {sortedEntries.map(([categoryType, categories]) => {
                            const selectedCategory = categories[0];
                            return (
                              <div key={categoryType}>
                                <label className="block text-sm font-bold text-gray-700 mb-2">
                                  {categoryTypeNames[categoryType] || categoryType}
                                </label>
                                <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                                  {selectedCategory ? (
                                    <p className="text-gray-900 font-semibold">{selectedCategory.name}</p>
                                  ) : (
                                    <p className="text-gray-400">未选择</p>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  );
                })()}

              {/* 段落6: 重要里程碑 */}
              <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-yellow-50 via-amber-50 to-orange-50 px-6 py-5 border-b-2 border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-yellow-500 rounded-lg">
                      <CheckCircle2 className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900">重要里程碑</h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">实施启动</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        {project.milestone_implementation_start ? (
                          <p className="text-gray-900 font-semibold">
                            {new Date(project.milestone_implementation_start).toLocaleDateString('zh-CN')}
                          </p>
                        ) : (
                          <p className="text-gray-400">未设置</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">方案确认</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        {project.milestone_solution_confirmation ? (
                          <p className="text-gray-900 font-semibold">
                            {new Date(project.milestone_solution_confirmation).toLocaleDateString('zh-CN')}
                          </p>
                        ) : (
                          <p className="text-gray-400">未设置</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">交付上线</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        {project.milestone_delivery_online ? (
                          <p className="text-gray-900 font-semibold">
                            {new Date(project.milestone_delivery_online).toLocaleDateString('zh-CN')}
                          </p>
                        ) : (
                          <p className="text-gray-400">未设置</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-gray-700 mb-2">项目验收</label>
                      <div className="bg-gray-50 rounded-xl p-3 border-2 border-gray-200">
                        {project.milestone_project_acceptance ? (
                          <p className="text-gray-900 font-semibold">
                            {new Date(project.milestone_project_acceptance).toLocaleDateString('zh-CN')}
                          </p>
                        ) : (
                          <p className="text-gray-400">未设置</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 健康度卡片 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div className="flex items-center gap-4 mb-5">
                  <div className="p-3 bg-gradient-to-br from-green-100 to-green-200 rounded-xl shadow-sm">
                    <CheckCircle2 className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-gray-700">健康度</h2>
                    <p className="text-3xl font-bold text-green-600 mt-1">
                      {project.health_score.toFixed(1)}
                    </p>
                  </div>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-500 flex items-center justify-end pr-2 shadow-sm"
                    style={{ width: `${project.health_score}%` }}
                  >
                    {project.health_score > 10 && (
                      <span className="text-xs text-white font-semibold">
                        {project.health_score.toFixed(0)}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* 快速链接 */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">相关功能</h2>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <Link
                    href={`/projects/tasks?project_id=${project.id}`}
                    className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 group"
                  >
                    <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                      <CheckCircle2 className="w-5 h-5 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600">
                      任务管理
                    </span>
                  </Link>
                  <Link
                    href={`/projects/milestones?project_id=${project.id}`}
                    className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-all duration-200 group"
                  >
                    <div className="p-2 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
                      <Calendar className="w-5 h-5 text-purple-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-purple-600">
                      项目阶段
                    </span>
                  </Link>
                  <Link
                    href={`/projects/weekly-reports?project_id=${project.id}`}
                    className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-green-50 hover:border-green-300 transition-all duration-200 group"
                  >
                    <div className="p-2 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
                      <FileText className="w-5 h-5 text-green-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-green-600">
                      周报
                    </span>
                  </Link>
                  <Link
                    href={`/projects/risks?project_id=${project.id}`}
                    className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-red-50 hover:border-red-300 transition-all duration-200 group"
                  >
                    <div className="p-2 bg-red-100 rounded-lg group-hover:bg-red-200 transition-colors">
                      <AlertCircle className="w-5 h-5 text-red-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-red-600">
                      风险管理
                    </span>
                  </Link>
                  <Link
                    href={`/projects/plans?project_id=${project.id}`}
                    className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 transition-all duration-200 group"
                  >
                    <div className="p-2 bg-indigo-100 rounded-lg group-hover:bg-indigo-200 transition-colors">
                      <GanttIcon className="w-5 h-5 text-indigo-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-indigo-600">
                      项目计划
                    </span>
                  </Link>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'plans' && (
            <ProjectPlansByPhaseSection
              projectId={projectId}
              phases={phases}
              plans={plans}
              loadingPhases={loadingPhases}
              loadingPlans={loadingPlans}
              onRefresh={fetchPlans}
            />
          )}

          {activeTab === 'weekly-reports' && (
            <WeeklyReportsSection projectId={projectId} projectName={project.name} />
          )}

          {activeTab === 'monthly-reports' && (
            <MonthlyReportsSection projectId={projectId} projectName={project.name} />
          )}
        </div>
      </div>

      {/* 编辑模态框 */}
      {showEditModal && project && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 border-b-2 border-gray-200 px-6 py-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <Edit className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">编辑项目</h2>
              </div>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-2 rounded-lg hover:bg-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <div className="p-6 space-y-6">
                {/* 段落1: 基本信息 */}
                <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl border-2 border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-5 border-b-2 border-gray-200">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-500 rounded-lg">
                        <Building2 className="w-5 h-5 text-white" />
                      </div>
                      <h2 className="text-xl font-bold text-gray-900">基本信息</h2>
                    </div>
                  </div>
                  <div className="p-6 space-y-6">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-bold text-gray-700 mb-2">
                        项目名称 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-bold text-gray-700 mb-2">项目描述</label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        rows={4}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 resize-none bg-white"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">项目状态</label>
                        <select
                          value={formData.status}
                          onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                        >
                          <option value="planning">规划中</option>
                          <option value="active">进行中</option>
                          <option value="delayed">已延迟</option>
                          <option value="completed">已完成</option>
                          <option value="cancelled">已取消</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">优先级</label>
                        <select
                          value={formData.priority}
                          onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                        >
                          <option value="low">低</option>
                          <option value="medium">中</option>
                          <option value="high">高</option>
                          <option value="critical">紧急</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 段落2: 时间信息 */}
                <div className="bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 rounded-2xl border-2 border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 px-6 py-5 border-b-2 border-gray-200">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-500 rounded-lg">
                        <Calendar className="w-5 h-5 text-white" />
                      </div>
                      <h2 className="text-xl font-bold text-gray-900">时间信息</h2>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">计划开始日期</label>
                        <input
                          type="date"
                          value={formData.start_date}
                          onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 bg-white"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">计划结束日期</label>
                        <input
                          type="date"
                          value={formData.end_date}
                          onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 bg-white"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* 段落3: 人员信息 */}
                <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 rounded-2xl border-2 border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 px-6 py-5 border-b-2 border-gray-200">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-500 rounded-lg">
                        <Users className="w-5 h-5 text-white" />
                      </div>
                      <h2 className="text-xl font-bold text-gray-900">人员信息</h2>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">项目经理</label>
                        <select
                          value={formData.manager_id}
                          onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-white"
                        >
                          <option value="">请选择</option>
                          {users.map((user) => (
                            <option key={user.user_id} value={user.user_id}>
                              {user.display_name || user.username}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">填报人</label>
                        <select
                          value={formData.reporter_id}
                          onChange={(e) => setFormData({ ...formData, reporter_id: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-white"
                        >
                          <option value="">请选择</option>
                          {users.map((user) => (
                            <option key={user.user_id} value={user.user_id}>
                              {user.display_name || user.username}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 段落4: 预算与进度 */}
                <div className="bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 rounded-2xl border-2 border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 px-6 py-5 border-b-2 border-gray-200">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-orange-500 rounded-lg">
                        <DollarSign className="w-5 h-5 text-white" />
                      </div>
                      <h2 className="text-xl font-bold text-gray-900">预算与进度</h2>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">预算</label>
                        <input
                          type="number"
                          step="0.01"
                          value={formData.budget}
                          onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white"
                          placeholder="0.00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">进度 (%)</label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="100"
                          value={formData.progress_percent}
                          onChange={(e) =>
                            setFormData({ ...formData, progress_percent: e.target.value })
                          }
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white"
                          placeholder="0.0"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">健康度</label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="100"
                          value={formData.health_score}
                          onChange={(e) => setFormData({ ...formData, health_score: e.target.value })}
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white"
                          placeholder="0.0"
                        />
                      </div>
                    </div>

                    <div className="mt-6">
                      <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border-2 border-gray-200">
                        <input
                          type="checkbox"
                          checked={formData.requires_weekly_report}
                          onChange={(e) =>
                            setFormData({ ...formData, requires_weekly_report: e.target.checked })
                          }
                          className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                        />
                        <FileText className="w-5 h-5 text-gray-600" />
                        <label className="text-sm font-semibold text-gray-700 cursor-pointer">
                          是否编写周报
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 段落6: 重要里程碑 */}
                <div className="bg-gradient-to-r from-yellow-50 via-amber-50 to-orange-50 rounded-2xl border-2 border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-yellow-50 via-amber-50 to-orange-50 px-6 py-5 border-b-2 border-gray-200">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-yellow-500 rounded-lg">
                        <CheckCircle2 className="w-5 h-5 text-white" />
                      </div>
                      <h2 className="text-xl font-bold text-gray-900">重要里程碑</h2>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">实施启动</label>
                        <input
                          type="date"
                          value={formData.milestone_implementation_start}
                          onChange={(e) =>
                            setFormData({ ...formData, milestone_implementation_start: e.target.value })
                          }
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">方案确认</label>
                        <input
                          type="date"
                          value={formData.milestone_solution_confirmation}
                          onChange={(e) =>
                            setFormData({ ...formData, milestone_solution_confirmation: e.target.value })
                          }
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">交付上线</label>
                        <input
                          type="date"
                          value={formData.milestone_delivery_online}
                          onChange={(e) =>
                            setFormData({ ...formData, milestone_delivery_online: e.target.value })
                          }
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">项目验收</label>
                        <input
                          type="date"
                          value={formData.milestone_project_acceptance}
                          onChange={(e) =>
                            setFormData({ ...formData, milestone_project_acceptance: e.target.value })
                          }
                          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 bg-white"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* 基础数据分类选择 - 下拉框单选 */}
                {!loadingCategories &&
                  categories.length > 0 &&
                  (() => {
                    // 先过滤和分组
                    const grouped = categories
                      .filter((cat: any) => {
                        // 只允许的分类类型（白名单）
                        const allowedTypes = [
                          'project_phase',
                          'phase_status',
                          'application_domain',
                          'project_category',
                        ];
                        return allowedTypes.includes(cat.category_type);
                      })
                      .reduce((acc: any, cat: any) => {
                        if (!acc[cat.category_type]) {
                          acc[cat.category_type] = [];
                        }
                        acc[cat.category_type].push(cat);
                        return acc;
                      }, {});

                    // 处理重复的分类类型
                    const processed: Record<string, any[]> = {};
                    Object.entries(grouped).forEach(([type, items]: [string, any]) => {
                      if (!processed[type]) {
                        if (type === 'application_domain') {
                          // 对于应用领域，只保留指定的编码格式（01-、02-、...、99-）
                          const allowedCodes = [
                            '01-',
                            '02-',
                            '03-',
                            '04-',
                            '05-',
                            '06-',
                            '07-',
                            '08-',
                            '09-',
                            '10-',
                            '11-',
                            '12-',
                            '99-',
                          ];
                          const filteredItems = (items as any[]).filter((item) => {
                            if (!item.code) return false;
                            return allowedCodes.some((code) => item.code.startsWith(code));
                          });
                          // 按编码排序
                          const sortedItems = filteredItems.sort((a, b) => {
                            const aCode = a.code || '';
                            const bCode = b.code || '';
                            return aCode.localeCompare(bCode);
                          });
                          processed[type] = sortedItems;
                        } else {
                          // 对于有编码的分类，优先保留有编码的
                          const sortedItems = (items as any[]).sort((a, b) => {
                            const aHasCode = a.code && /^\d{2}-/.test(a.code);
                            const bHasCode = b.code && /^\d{2}-/.test(b.code);
                            if (aHasCode && !bHasCode) return -1;
                            if (!aHasCode && bHasCode) return 1;
                            return 0;
                          });
                          processed[type] = sortedItems;
                        }
                      }
                    });

                    // 排序
                    const categoryOrder: Record<string, number> = {
                      project_phase: 1,
                      phase_status: 2,
                      application_domain: 3,
                      project_category: 4,
                    };

                    const sortedEntries = Object.entries(processed).sort(([typeA], [typeB]) => {
                      const orderA = categoryOrder[typeA] ?? 999;
                      const orderB = categoryOrder[typeB] ?? 999;
                      return orderA - orderB;
                    });

                    const categoryTypeNames: Record<string, string> = {
                      project_phase: '项目阶段',
                      phase_status: '阶段状态',
                      application_domain: '应用领域',
                      project_category: '项目分类',
                    };

                    return (
                      <div className="bg-gradient-to-r from-indigo-50 via-blue-50 to-cyan-50 rounded-2xl border-2 border-gray-100 overflow-hidden">
                        <div className="bg-gradient-to-r from-indigo-50 via-blue-50 to-cyan-50 px-6 py-5 border-b-2 border-gray-200">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-500 rounded-lg">
                              <Target className="w-5 h-5 text-white" />
                            </div>
                            <h2 className="text-xl font-bold text-gray-900">项目分类</h2>
                          </div>
                        </div>
                        <div className="p-6">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {sortedEntries.map(([type, items]: [string, any]) => (
                              <div key={type}>
                                <label className="block text-sm font-bold text-gray-700 mb-2">
                                  {categoryTypeNames[type] || type}
                                </label>
                                <select
                                  value={formData.basic_data_categories[type] || ''}
                                  onChange={(e) => {
                                    setFormData({
                                      ...formData,
                                      basic_data_categories: {
                                        ...formData.basic_data_categories,
                                        [type]: e.target.value || '',
                                      },
                                    });
                                  }}
                                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200 bg-white"
                                >
                                  <option value="">请选择</option>
                                  {items.map((cat: any) => (
                                    <option key={cat.id} value={cat.id}>
                                      {cat.name}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
              </div>
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-5 border-t-2 border-gray-200 flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowEditModal(false)}
                  className="px-8 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-semibold shadow-md hover:shadow-lg"
                >
                  取消
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold shadow-lg hover:shadow-xl"
                >
                  <Save className="h-5 w-5" />
                  {saving ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 删除确认对话框 */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-2">确认删除</h2>
              <p className="text-gray-600 mb-6">
                您确定要删除项目 <span className="font-semibold">{project?.name}</span>{' '}
                吗？此操作无法撤销。
              </p>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleting ? '删除中...' : '确认删除'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 按阶段展示项目计划的组件
interface ProjectPlansByPhaseSectionProps {
  projectId: string;
  phases: ProjectPhase[];
  plans: ProjectPlan[];
  loadingPhases: boolean;
  loadingPlans: boolean;
  onRefresh: () => void;
}

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
  phase_id?: string;
}

function ProjectPlansByPhaseSection({
  projectId,
  phases,
  plans,
  loadingPhases,
  loadingPlans,
  onRefresh,
}: ProjectPlansByPhaseSectionProps) {
  const router = useRouter();
  const [planTrees, setPlanTrees] = useState<Record<string, PlanTreeNode[]>>({});
  const [loadingTrees, setLoadingTrees] = useState<Record<string, boolean>>({});
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<'phase' | 'task' | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 获取计划树形结构
  const fetchPlanTree = async (planId: string) => {
    if (planTrees[planId] || loadingTrees[planId]) return;

    setLoadingTrees((prev) => ({ ...prev, [planId]: true }));
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}/plans/${planId}/tree`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPlanTrees((prev) => ({ ...prev, [planId]: data.tree || [] }));
      } else {
        // 处理非 200 响应
        const errorText = await response.text().catch(() => '未知错误');
        console.error(`获取计划树形结构失败: HTTP ${response.status}`, errorText);
        // 设置空数组，避免页面崩溃
        setPlanTrees((prev) => ({ ...prev, [planId]: [] }));
        // 如果是 500 错误，设置错误状态但不阻止页面渲染
        if (response.status === 500) {
          setError('获取计划数据时发生服务器错误，部分功能可能不可用');
        }
      }
    } catch (error) {
      console.error('获取计划树形结构失败:', error);
      // 设置空数组，避免页面崩溃
      setPlanTrees((prev) => ({ ...prev, [planId]: [] }));
    } finally {
      setLoadingTrees((prev) => ({ ...prev, [planId]: false }));
    }
  };

  // 当计划列表变化时，获取所有计划的树形结构
  useEffect(() => {
    plans.forEach((plan) => {
      if (plan.id && !planTrees[plan.id]) {
        fetchPlanTree(plan.id);
      }
    });
  }, [plans]);

  // 获取主计划（通常只有一个）
  const mainPlan = plans.length > 0 ? plans[0] : null;

  const handleCreateTask = async (planId: string, phaseId: string) => {
    // 跳转到计划详情页面，并自动打开创建任务对话框
    router.push(`/projects/plans/${planId}?projectId=${projectId}&phaseId=${phaseId}&action=createTask`);
  };

  if (loadingPhases || loadingPlans) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (phases.length === 0) {
    return (
      <div className="text-center py-12">
        <GanttIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p className="text-gray-600 mb-2">暂无项目阶段</p>
        <p className="text-sm text-gray-500">请先创建项目阶段</p>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="text-center py-12">
        <GanttIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p className="text-gray-600 mb-2">暂无项目计划</p>
        <p className="text-sm text-gray-500">系统将基于"标准信息化项目管理模板"自动创建计划</p>
      </div>
    );
  }

  // 如果有主计划，展示树形表格
  if (mainPlan) {
    const tree = planTrees[mainPlan.id] || [];
    const isLoading = loadingTrees[mainPlan.id];

    const handleUpdateTask = async (taskId: string, data: Partial<any>) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
        const token = getAccessToken();

        const response = await fetch(
          `${apiUrl}/api/v1/projects/${projectId}/plans/${mainPlan.id}/tasks/${taskId}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: token ? `Bearer ${token}` : '',
            },
            body: JSON.stringify(data),
          }
        );

        if (response.ok) {
          // 刷新树形结构
          await fetchPlanTree(mainPlan.id);
          onRefresh();
        } else {
          const errorText = await response.text().catch(() => '未知错误');
          console.error(`更新任务失败: HTTP ${response.status}`, errorText);
          // 可以在这里添加用户提示，比如 toast 通知
        }
      } catch (error) {
        console.error('更新任务失败:', error);
        // 确保错误不会导致页面崩溃
      }
    };

    const handleMoveTask = async (taskId: string, newParentId: string | null, newIndex: number) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
        const token = getAccessToken();

        const response = await fetch(
          `${apiUrl}/api/v1/projects/${projectId}/plans/${mainPlan.id}/tasks/${taskId}/move`,
          {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              Authorization: token ? `Bearer ${token}` : '',
            },
            body: JSON.stringify({
              new_parent_id: newParentId,
              new_index: newIndex,
            }),
          }
        );

        if (response.ok) {
          // 刷新树形结构
          await fetchPlanTree(mainPlan.id);
          onRefresh();
        } else {
          const errorText = await response.text().catch(() => '未知错误');
          console.error(`移动任务失败: HTTP ${response.status}`, errorText);
        }
      } catch (error) {
        console.error('移动任务失败:', error);
        // 确保错误不会导致页面崩溃
      }
    };

    return (
      <div className="space-y-4">
        {error && (
          <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
        )}

        {/* 计划信息卡片 - 美化 */}
        <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-xl border-2 border-indigo-200 p-6 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
                <GanttIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-1">{mainPlan.name}</h3>
                {mainPlan.description && (
                  <p className="text-sm text-gray-600">{mainPlan.description}</p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  {mainPlan.is_active && (
                    <span className="px-3 py-1 bg-gradient-to-r from-green-400 to-emerald-500 text-white rounded-full text-xs font-semibold shadow-md">
                      活跃计划
                    </span>
                  )}
                  {mainPlan.version && (
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                      版本 {mainPlan.version}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <Link
              href={`/projects/plans/${mainPlan.id}?projectId=${projectId}`}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all font-semibold shadow-lg hover:shadow-xl flex items-center gap-2"
            >
              <FileText className="w-5 h-5" />
              查看详情
            </Link>
          </div>
        </div>

        {/* 左右分栏布局 */}
        <ErrorBoundary
          fallback={
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <AlertCircle className="w-6 h-6 text-yellow-600" />
                <div>
                  <h3 className="font-semibold text-yellow-900">组件加载失败</h3>
                  <p className="text-sm text-yellow-700 mt-1">
                    组件加载失败。请刷新页面重试，或使用其他功能。
                  </p>
                </div>
              </div>
            </div>
          }
        >
          <div className="flex gap-6 h-[calc(100vh-250px)] min-h-[600px]">
            {/* 左侧：树形结构 - 美化 */}
            <div className="w-1/3 bg-white rounded-xl shadow-lg border-2 border-gray-100 p-4 overflow-hidden flex flex-col">
              <PlanTreeView
                tree={tree}
                loading={isLoading}
                selectedNodeId={selectedNodeId || undefined}
                onAddTask={(parentId, parentType) => {
                  // 设置选中节点，以便在右侧任务列表中创建任务
                  setSelectedNodeId(parentId);
                  setSelectedNodeType(parentType);
                  // 触发右侧任务列表的创建任务功能
                  setTimeout(() => {
                    const event = new CustomEvent('createTask', { detail: { parentId, parentType } });
                    window.dispatchEvent(event);
                  }, 100);
                }}
                onEditTask={(taskId) => {
                  router.push(`/projects/plans/${mainPlan.id}?projectId=${projectId}&taskId=${taskId}&action=editTask`);
                }}
                onDeleteTask={async (taskId) => {
                  if (confirm('确定要删除这个任务吗？')) {
                    try {
                      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
                      const token = getAccessToken();

                      const response = await fetch(
                        `${apiUrl}/api/v1/projects/${projectId}/plans/${mainPlan.id}/tasks/${taskId}`,
                        {
                          method: 'DELETE',
                          headers: {
                            Authorization: token ? `Bearer ${token}` : '',
                          },
                        }
                      );

                      if (response.ok) {
                        await fetchPlanTree(mainPlan.id);
                        onRefresh();
                        // 如果删除的是当前选中的节点，清空选中状态
                        if (selectedNodeId === taskId) {
                          setSelectedNodeId(null);
                          setSelectedNodeType(null);
                        }
                      } else {
                        const errorText = await response.text().catch(() => '未知错误');
                        console.error(`删除任务失败: HTTP ${response.status}`, errorText);
                        setError(`删除任务失败: ${response.status === 500 ? '服务器错误' : '操作失败'}`);
                      }
                    } catch (error) {
                      console.error('删除任务失败:', error);
                      setError('删除任务失败，请稍后重试');
                    }
                  }
                }}
                onNodeSelect={(nodeId, nodeType) => {
                  setSelectedNodeId(nodeId);
                  setSelectedNodeType(nodeType);
                }}
              />
            </div>

            {/* 右侧：任务列表 - 美化 */}
            <div className="flex-1 bg-white rounded-xl shadow-lg border-2 border-gray-100 p-6 overflow-hidden flex flex-col">
              {selectedNodeId && selectedNodeType ? (
                <div className="flex-1 overflow-hidden flex flex-col">
                  <TaskList
                    nodeId={selectedNodeId}
                    nodeType={selectedNodeType}
                    projectId={projectId}
                    planId={mainPlan.id}
                    tree={tree}
                    onRefresh={() => {
                      fetchPlanTree(mainPlan.id);
                      onRefresh();
                    }}
                  />
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="p-6 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl mb-4 inline-block">
                      <FileText className="w-20 h-20 mx-auto text-indigo-300" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">选择节点查看任务</h3>
                    <p className="text-gray-600 mb-4">点击左侧的阶段或任务节点即可查看对应的任务列表</p>
                    <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                      <ChevronRight className="w-4 h-4" />
                      <span>选择节点开始查看</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </ErrorBoundary>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {phases.map((phase) => (
        <div
          key={phase.id}
          className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{phase.name}</h3>
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                  阶段 {phase.sequence}
                </span>
              </div>
              {phase.description && (
                <p className="text-sm text-gray-600 mb-2">{phase.description}</p>
              )}
              <div className="flex items-center gap-4 text-sm text-gray-500">
                {phase.start_date && (
                  <span>
                    <Calendar className="w-4 h-4 inline mr-1" />
                    开始: {new Date(phase.start_date).toLocaleDateString()}
                  </span>
                )}
                {phase.end_date && (
                  <span>
                    <Clock className="w-4 h-4 inline mr-1" />
                    结束: {new Date(phase.end_date).toLocaleDateString()}
                  </span>
                )}
                <span>进度: {phase.progress_percent.toFixed(0)}%</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// 带选择功能的树节点组件
interface TreeNodeWithSelectProps {
  node: PlanTreeNode;
  level: number;
  selectedNodeId: string | null;
  onSelect: (node: PlanTreeNode) => void;
  onAddTask?: (phaseId: string) => void;
}

function TreeNodeWithSelect({
  node,
  level,
  selectedNodeId,
  onSelect,
  onAddTask,
}: TreeNodeWithSelectProps) {
  const [expanded, setExpanded] = useState(level < 2);

  const hasChildren = node.children && node.children.length > 0;
  const isPhase = node.type === 'phase';
  const isReadonly = node.is_readonly;
  const isSelected = selectedNodeId === node.id;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      setExpanded(!expanded);
    }
  };

  const handleClick = () => {
    onSelect(node);
  };

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 py-2 px-3 rounded cursor-pointer transition-colors ${
          isSelected
            ? 'bg-indigo-100 border border-indigo-300'
            : isPhase
              ? 'bg-blue-50 hover:bg-blue-100'
              : 'hover:bg-gray-50'
        }`}
        style={{ paddingLeft: `${level * 24 + 12}px` }}
        onClick={handleClick}
      >
        {hasChildren && (
          <button
            onClick={handleToggle}
            className="flex items-center justify-center w-5 h-5 hover:bg-gray-200 rounded"
          >
            {expanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        )}
        {!hasChildren && <div className="w-5" />}

        <div className="flex items-center gap-2 flex-1 min-w-0">
          {isPhase ? (
            <Folder className="w-4 h-4 text-blue-500 flex-shrink-0" />
          ) : (
            <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
          )}

          <span
            className={`flex-1 truncate ${
              isReadonly ? 'text-gray-600' : isSelected ? 'text-indigo-900 font-medium' : 'text-gray-900'
            }`}
          >
            {node.name}
          </span>

          {isReadonly && (
            <Lock className="w-4 h-4 text-gray-400" />
          )}

          {node.progress_percent !== undefined && (
            <span className="text-xs text-gray-500">
              {node.progress_percent}%
            </span>
          )}
        </div>

        {isPhase && onAddTask && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddTask(node.id);
            }}
            className="p-1 hover:bg-gray-200 rounded"
            title="添加任务"
          >
            <Plus className="w-4 h-4 text-gray-500" />
          </button>
        )}
      </div>

      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <TreeNodeWithSelect
              key={child.id}
              node={child}
              level={level + 1}
              selectedNodeId={selectedNodeId}
              onSelect={onSelect}
              onAddTask={onAddTask}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// 周报组件 - 创建表单
interface WeeklyReportsSectionProps {
  projectId: string;
  projectName: string;
}

function WeeklyReportsSection({ projectId, projectName }: WeeklyReportsSectionProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [formData, setFormData] = useState({
    project_id: projectId,
    week_number: '',
    report_date: new Date().toISOString().split('T')[0],
    content_plan: '',
    content_achievement: '',
    issues_risks: '',
    next_week_plan: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 计算指定月份的所有周
  const calculateWeeksInMonth = (year: number, month: number) => {
    const weeks: Array<{ weekNumber: number; weekLabel: string; startDate: Date; endDate: Date }> = [];
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);

    const currentDate = new Date(firstDay);
    let weekNumber = 1;

    while (currentDate <= lastDay) {
      const dayOfWeek = currentDate.getDay();
      const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
      const weekStart = new Date(currentDate);
      weekStart.setDate(weekStart.getDate() - daysToMonday);

      if (weekStart < firstDay) {
        weekStart.setTime(firstDay.getTime());
      }

      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 6);

      if (weekEnd > lastDay) {
        weekEnd.setTime(lastDay.getTime());
      }

      if (weekStart <= lastDay && weekEnd >= firstDay) {
        const formatDate = (date: Date) => {
          const m = date.getMonth() + 1;
          const d = date.getDate();
          return `${m}月${d}日`;
        };
        const weekLabel = `第${weekNumber}周 (${formatDate(weekStart)} - ${formatDate(weekEnd)})`;

        weeks.push({
          weekNumber,
          weekLabel,
          startDate: new Date(weekStart),
          endDate: new Date(weekEnd),
        });
        weekNumber++;
      }

      currentDate.setDate(weekEnd.getDate() + 1);
    }

    return weeks;
  };

  const getCurrentWeekNumber = (weeks: Array<{ weekNumber: number; startDate: Date; endDate: Date }>) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (const week of weeks) {
      const start = new Date(week.startDate);
      start.setHours(0, 0, 0, 0);
      const end = new Date(week.endDate);
      end.setHours(23, 59, 59, 999);

      if (today >= start && today <= end) {
        return week.weekNumber;
      }
    }

    return null;
  };

  const getWeeksForMonth = () => {
    const [year, month] = selectedMonth.split('-').map(Number);
    return calculateWeeksInMonth(year, month);
  };

  useEffect(() => {
    const weeks = getWeeksForMonth();
    const currentWeek = getCurrentWeekNumber(weeks);

    if (currentWeek && weeks.length > 0) {
      const week = weeks.find((w) => w.weekNumber === currentWeek);
      if (week) {
        setFormData((prev) => ({
          ...prev,
          week_number: currentWeek.toString(),
          report_date: week.startDate.toISOString().split('T')[0],
        }));
      }
    } else if (weeks.length > 0) {
      const firstWeek = weeks[0];
      setFormData((prev) => ({
        ...prev,
        week_number: firstWeek.weekNumber.toString(),
        report_date: firstWeek.startDate.toISOString().split('T')[0],
      }));
    }
  }, [selectedMonth]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const payload = {
        ...formData,
        week_number: formData.week_number ? parseInt(formData.week_number) : null,
      };

      const response = await fetch(`${apiUrl}/api/v1/weekly-reports`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setSuccessMessage('周报创建成功！');
        setTimeout(() => {
          setSuccessMessage(null);
          // 重置表单
          setFormData({
            project_id: projectId,
            week_number: '',
            report_date: new Date().toISOString().split('T')[0],
            content_plan: '',
            content_achievement: '',
            issues_risks: '',
            next_week_plan: '',
          });
        }, 2000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '创建周报失败' }));
        setError(errorData.detail || '创建周报失败');
      }
    } catch (error: any) {
      console.error('创建周报失败:', error);
      setError(error?.message || '创建周报失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
      <ErrorMessage message={successMessage} type="success" onClose={() => setSuccessMessage(null)} autoClose />

      {/* 标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">创建周报</h2>
        <p className="text-sm text-gray-600 mt-1">为项目 {projectName} 创建新的周报</p>
      </div>

      {/* 创建表单 */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 overflow-hidden"
      >
        <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-5 border-b-2 border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-md">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            周报信息
          </h3>
        </div>
        <div className="p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                选择月份 <span className="text-red-500">*</span>
              </label>
              <input
                type="month"
                required
                value={selectedMonth}
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                }}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                选择周数 <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.week_number}
                onChange={(e) => {
                  const weekNumber = parseInt(e.target.value);
                  const weeks = getWeeksForMonth();
                  const selectedWeek = weeks.find((w) => w.weekNumber === weekNumber);
                  if (selectedWeek) {
                    setFormData({
                      ...formData,
                      week_number: e.target.value,
                      report_date: selectedWeek.startDate.toISOString().split('T')[0],
                    });
                  }
                }}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              >
                <option value="">请选择周数</option>
                {getWeeksForMonth().map((week) => (
                  <option key={week.weekNumber} value={week.weekNumber}>
                    {week.weekLabel}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                报告日期 <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                required
                value={formData.report_date}
                onChange={(e) => setFormData({ ...formData, report_date: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">默认为所选周的开始日期，可手动调整</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">本周计划内容</label>
            <textarea
              value={formData.content_plan}
              onChange={(e) => setFormData({ ...formData, content_plan: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本周计划完成的工作内容..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">本周完成成果</label>
            <textarea
              value={formData.content_achievement}
              onChange={(e) => setFormData({ ...formData, content_achievement: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本周实际完成的工作成果..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">问题与风险</label>
            <textarea
              value={formData.issues_risks}
              onChange={(e) => setFormData({ ...formData, issues_risks: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本周遇到的问题和风险..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">下周计划</label>
            <textarea
              value={formData.next_week_plan}
              onChange={(e) => setFormData({ ...formData, next_week_plan: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述下周计划完成的工作内容..."
            />
          </div>
        </div>
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-t-2 border-gray-200 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.push(`/projects/weekly-reports?project_id=${projectId}`)}
            className="px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm hover:shadow-md"
          >
            查看周报列表
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg hover:shadow-xl"
          >
            <Save className="h-5 w-5" />
            {loading ? '创建中...' : '创建周报'}
          </button>
        </div>
      </form>
    </div>
  );
}

// 月报组件
interface MonthlyReportsSectionProps {
  projectId: string;
  projectName: string;
}

function MonthlyReportsSection({ projectId, projectName }: MonthlyReportsSectionProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    project_id: projectId,
    report_month: new Date().toISOString().slice(0, 7), // YYYY-MM格式
    summary: '',
    achievements: '',
    challenges: '',
    next_month_plan: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/monthly-reports`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSuccessMessage('月报创建成功！');
        setTimeout(() => {
          setSuccessMessage(null);
          // 重置表单
          setFormData({
            project_id: projectId,
            report_month: new Date().toISOString().slice(0, 7),
            summary: '',
            achievements: '',
            challenges: '',
            next_month_plan: '',
          });
        }, 2000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: '创建月报失败' }));
        setError(errorData.detail || '创建月报失败');
      }
    } catch (error: any) {
      console.error('创建月报失败:', error);
      setError(error?.message || '创建月报失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
      <ErrorMessage message={successMessage} type="success" onClose={() => setSuccessMessage(null)} autoClose />

      {/* 标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">创建月报</h2>
        <p className="text-sm text-gray-600 mt-1">为项目 {projectName} 创建新的月报</p>
      </div>

      {/* 创建表单 */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 overflow-hidden"
      >
        <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 px-6 py-5 border-b-2 border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg shadow-md">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            月报信息
          </h3>
        </div>
        <div className="p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                报告月份 <span className="text-red-500">*</span>
              </label>
              <input
                type="month"
                required
                value={formData.report_month}
                onChange={(e) => setFormData({ ...formData, report_month: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">月度总结</label>
            <textarea
              value={formData.summary}
              onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="本月项目进展总结..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">主要成果</label>
            <textarea
              value={formData.achievements}
              onChange={(e) => setFormData({ ...formData, achievements: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本月完成的主要工作成果..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">挑战与问题</label>
            <textarea
              value={formData.challenges}
              onChange={(e) => setFormData({ ...formData, challenges: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本月遇到的挑战和问题..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">下月计划</label>
            <textarea
              value={formData.next_month_plan}
              onChange={(e) => setFormData({ ...formData, next_month_plan: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述下月计划完成的工作内容..."
            />
          </div>
        </div>
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-t-2 border-gray-200 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.push(`/projects/monthly-reports?project_id=${projectId}`)}
            className="px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm hover:shadow-md"
          >
            查看月报列表
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 text-white rounded-xl hover:from-purple-700 hover:via-pink-700 hover:to-rose-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg hover:shadow-xl"
          >
            <Save className="h-5 w-5" />
            {loading ? '创建中...' : '创建月报'}
          </button>
        </div>
      </form>
    </div>
  );
}
