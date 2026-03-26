'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import {
  ArrowLeft,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle,
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
} from 'lucide-react';
import Link from 'next/link';
import { getUsers, User } from '@/lib/api/admin';
import ProjectPhaseProgress from '@/components/ProjectPhaseProgress';
import ProjectPlansSection from '@/components/ProjectPlansSection';
import PlanTreeView from '@/components/ProjectPlans/PlanTreeView';
import PlanTreeTable from '@/components/ProjectPlans/PlanTreeTable';
import PlanExcelTable from '@/components/ProjectPlans/PlanExcelTable';
import TemplateSelector from '@/components/ProjectPlans/TemplateSelector';
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
  const [activeTab, setActiveTab] = useState<'overview' | 'plans'>('overview');
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
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/basic-data/categories?limit=1000`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCategories(data.items || []);
      }
    } catch (error) {
      console.error('加载基础数据分类失败:', error);
    } finally {
      setLoadingCategories(false);
    }
  };

  const fetchPhases = async () => {
    try {
      setLoadingPhases(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/project-phases?project_id=${projectId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const sortedPhases = (data.items || []).sort((a: ProjectPhase, b: ProjectPhase) =>
          a.sequence - b.sequence
        );
        setPhases(sortedPhases);
        // 如果阶段存在但没有对应的计划，自动创建计划
        await ensurePlansForPhases(sortedPhases);
      }
    } catch (error) {
      console.error('获取项目阶段失败:', error);
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
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/${projectId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProject(data);

        // 将项目名称存储到sessionStorage，供面包屑导航使用
        if (typeof window !== 'undefined' && data.name) {
          sessionStorage.setItem(`project_name_${projectId}`, data.name);
        }

        // 初始化表单数据
        // 将分类数组转换为对象，每个分类类型对应一个分类ID（单选）
        const categoryMap: Record<string, string> = {};
        if (data.basic_data_categories && Array.isArray(data.basic_data_categories)) {
          data.basic_data_categories.forEach((cat: any) => {
            // 如果该分类类型还没有值，则设置（只保留第一个）
            if (!categoryMap[cat.category_type]) {
              categoryMap[cat.category_type] = cat.id;
            }
          });
        }

        setFormData({
          name: data.name || '',
          description: data.description || '',
          status: data.status || '',
          priority: data.priority || '',
          manager_id: data.manager_id || '',
          reporter_id: data.reporter_id || '',
          start_date: data.start_date ? data.start_date.split('T')[0] : '',
          end_date: data.end_date ? data.end_date.split('T')[0] : '',
          budget: data.budget?.toString() || '',
          progress_percent: data.progress_percent?.toString() || '',
          health_score: data.health_score?.toString() || '',
          basic_data_categories: categoryMap,
          milestone_implementation_start: data.milestone_implementation_start
            ? data.milestone_implementation_start.split('T')[0]
            : '',
          milestone_solution_confirmation: data.milestone_solution_confirmation
            ? data.milestone_solution_confirmation.split('T')[0]
            : '',
          milestone_delivery_online: data.milestone_delivery_online
            ? data.milestone_delivery_online.split('T')[0]
            : '',
          milestone_project_acceptance: data.milestone_project_acceptance
            ? data.milestone_project_acceptance.split('T')[0]
            : '',
          requires_weekly_report: data.requires_weekly_report || false,
        });
      } else {
        setError('获取项目详情失败');
      }
    } catch (error) {
      console.error('获取项目详情失败:', error);
      setError('网络错误');
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
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <>
              {/* 项目信息卡片 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-6">
        <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>
                  项目编码:{' '}
                  <span className="font-mono font-semibold text-gray-900">
                    {project.project_code}
                  </span>
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <span
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border shadow-sm ${getStatusColor(project.status)}`}
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
        <div className="p-6">
          {/* 项目分类信息 */}
          {project.basic_data_categories &&
            project.basic_data_categories.length > 0 &&
            (() => {
              // 只允许的分类类型（白名单）
              const allowedTypes = [
                'project_phase',
                'phase_status',
                'application_domain',
                'project_category',
              ];

              // 过滤和去重分类，只保留允许的类型
              const filtered = project.basic_data_categories.filter((cat) =>
                allowedTypes.includes(cat.category_type)
              );

              // 按类型分组并去重
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

              // 只保留第一个出现的分类类型
              const processed: Record<string, BasicDataCategory[]> = {};
              Object.entries(grouped).forEach(([type, categories]) => {
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
                    const filtered = categories.filter((cat) => {
                      if (!cat.code) return false;
                      return allowedCodes.some((code) => cat.code.startsWith(code));
                    });
                    // 按编码排序
                    const sorted = filtered.sort((a, b) => {
                      const aCode = a.code || '';
                      const bCode = b.code || '';
                      return aCode.localeCompare(bCode);
                    });
                    processed[type] = sorted;
                  } else {
                    // 对于有编码的分类，优先显示有编码的
                    const sorted = categories.sort((a, b) => {
                      const aHasCode = a.code && /^\d{2}-/.test(a.code);
                      const bHasCode = b.code && /^\d{2}-/.test(b.code);
                      if (aHasCode && !bHasCode) return -1;
                      if (!aHasCode && bHasCode) return 1;
                      return 0;
                    });
                    processed[type] = sorted;
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
                <div className="mb-6 pb-6 border-b border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900 mb-4">项目分类</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {sortedEntries.map(([categoryType, categories]) => {
                      const selectedCategory = categories[0];
                      return (
                        <div key={categoryType} className="bg-gray-50 rounded-lg p-3">
                          <p className="text-xs font-medium text-gray-500 mb-1.5">
                            {categoryTypeNames[categoryType] || categoryType}
                          </p>
                          {selectedCategory ? (
                            <p className="text-sm font-semibold text-gray-900">
                              {selectedCategory.name}
                            </p>
                          ) : (
                            <p className="text-sm text-gray-400">未选择</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

          {/* 项目详细信息 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 项目描述 */}
            {project.description && (
              <div className="md:col-span-2">
                <p className="text-sm font-medium text-gray-700 mb-1">项目描述</p>
                <p className="text-gray-700 whitespace-pre-wrap">{project.description}</p>
              </div>
            )}

            {/* 项目经理 */}
            {project.manager_name && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">项目经理</p>
                <p className="text-gray-900">{project.manager_name}</p>
              </div>
            )}

            {/* 填报人 */}
            {project.reporter_name && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">填报人</p>
                <p className="text-gray-900">{project.reporter_name}</p>
              </div>
            )}

            {/* 是否编写周报 */}
            <div>
              <p className="text-sm font-medium text-gray-700 mb-1">是否编写周报</p>
              <p className="text-gray-900">
                {project.requires_weekly_report ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    是
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    否
                  </span>
                )}
              </p>
            </div>

            {/* 开始日期 */}
            {project.start_date && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">开始日期</p>
                <p className="text-gray-900">{new Date(project.start_date).toLocaleDateString()}</p>
              </div>
            )}

            {/* 结束日期 */}
            {project.end_date && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">结束日期</p>
                <p className="text-gray-900">{new Date(project.end_date).toLocaleDateString()}</p>
              </div>
            )}
          </div>
        </div>
      </div>

              {/* 重要里程碑 - 新增区块 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2.5 bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-xl shadow-sm">
                    <Calendar className="w-5 h-5 text-yellow-600" />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-900">重要里程碑</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">实施启动</p>
                    {project.milestone_implementation_start ? (
                      <p className="text-base font-semibold text-gray-900">
                        {new Date(project.milestone_implementation_start).toLocaleDateString('zh-CN')}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-400">未设置</p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">方案确认</p>
                    {project.milestone_solution_confirmation ? (
                      <p className="text-base font-semibold text-gray-900">
                        {new Date(project.milestone_solution_confirmation).toLocaleDateString('zh-CN')}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-400">未设置</p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">交付上线</p>
                    {project.milestone_delivery_online ? (
                      <p className="text-base font-semibold text-gray-900">
                        {new Date(project.milestone_delivery_online).toLocaleDateString('zh-CN')}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-400">未设置</p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">项目验收</p>
                    {project.milestone_project_acceptance ? (
                      <p className="text-base font-semibold text-gray-900">
                        {new Date(project.milestone_project_acceptance).toLocaleDateString('zh-CN')}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-400">未设置</p>
                    )}
                  </div>
                </div>
              </div>

              {/* 健康度卡片 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div className="flex items-center gap-4 mb-5">
                  <div className="p-3 bg-gradient-to-br from-green-100 to-green-200 rounded-xl shadow-sm">
                    <CheckCircle className="w-6 h-6 text-green-600" />
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
                      <CheckCircle className="w-5 h-5 text-blue-600" />
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
            </>
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
        </div>
      </div>

      {/* 编辑模态框 */}
      {showEditModal && project && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">编辑项目</h2>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <div className="p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">项目名称</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">项目描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">项目状态</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    >
                      <option value="planning">规划中</option>
                      <option value="active">进行中</option>
                      <option value="delayed">已延迟</option>
                      <option value="completed">已完成</option>
                      <option value="cancelled">已取消</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    >
                      <option value="low">低</option>
                      <option value="medium">中</option>
                      <option value="high">高</option>
                      <option value="critical">紧急</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">项目经理</label>
                    <select
                      value={formData.manager_id}
                      onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
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
                    <label className="block text-sm font-medium text-gray-700 mb-1">填报人</label>
                    <select
                      value={formData.reporter_id}
                      onChange={(e) => setFormData({ ...formData, reporter_id: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
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

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">开始日期</label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">结束日期</label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.requires_weekly_report}
                      onChange={(e) =>
                        setFormData({ ...formData, requires_weekly_report: e.target.checked })
                      }
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-700">是否编写周报</span>
                  </label>
                </div>

                {/* 重要里程碑日期 */}
                <div className="border-t border-gray-200 pt-4">
                  <h3 className="text-sm font-semibold text-gray-900 mb-4">重要里程碑</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        实施启动
                      </label>
                      <input
                        type="date"
                        value={formData.milestone_implementation_start}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            milestone_implementation_start: e.target.value,
                          })
                        }
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        方案确认
                      </label>
                      <input
                        type="date"
                        value={formData.milestone_solution_confirmation}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            milestone_solution_confirmation: e.target.value,
                          })
                        }
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        交付上线
                      </label>
                      <input
                        type="date"
                        value={formData.milestone_delivery_online}
                        onChange={(e) =>
                          setFormData({ ...formData, milestone_delivery_online: e.target.value })
                        }
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        项目验收
                      </label>
                      <input
                        type="date"
                        value={formData.milestone_project_acceptance}
                        onChange={(e) =>
                          setFormData({ ...formData, milestone_project_acceptance: e.target.value })
                        }
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">预算</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.budget}
                      onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">进度 (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={formData.progress_percent}
                      onChange={(e) =>
                        setFormData({ ...formData, progress_percent: e.target.value })
                      }
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">健康度</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={formData.health_score}
                      onChange={(e) => setFormData({ ...formData, health_score: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                    />
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
                      <div className="border-t border-gray-200 pt-4">
                        <h3 className="text-sm font-semibold text-gray-900 mb-4">项目分类</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {sortedEntries.map(([type, items]: [string, any]) => (
                            <div key={type}>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
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
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
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
                    );
                  })()}
              </div>
              <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowEditModal(false)}
                  className="px-6 py-2.5 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  取消
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm"
                >
                  <Save className="w-4 h-4" />
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
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

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
      }
    } catch (error) {
      console.error('获取计划树形结构失败:', error);
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
        }
      } catch (error) {
        console.error('更新任务失败:', error);
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
        }
      } catch (error) {
        console.error('移动任务失败:', error);
      }
    };

    return (
      <div className="space-y-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <GanttIcon className="w-5 h-5 text-indigo-600" />
              <h3 className="text-lg font-semibold text-gray-900">{mainPlan.name}</h3>
              {mainPlan.is_active && (
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                  活跃
                </span>
              )}
            </div>
            <Link
              href={`/projects/plans/${mainPlan.id}?projectId=${projectId}`}
              className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              查看详情
            </Link>
          </div>
          {mainPlan.description && (
            <p className="text-sm text-gray-600">{mainPlan.description}</p>
          )}
        </div>

        <PlanExcelTable
          tree={tree}
          loading={isLoading}
          onAddTask={(phaseId) => {
            handleCreateTask(mainPlan.id, phaseId);
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
                }
              } catch (error) {
                console.error('删除任务失败:', error);
              }
            }
          }}
          onUpdateTask={handleUpdateTask}
          onMoveTask={handleMoveTask}
        />
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

