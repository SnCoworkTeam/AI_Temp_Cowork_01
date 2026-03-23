'use client';

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiGatewayClient } from '@/lib/api/client';
import { GanttChart } from '@/components/charts/GanttChart';
import { Calendar, Filter, Download, Building2, Layers, CheckCircle, Target, TrendingUp } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  project_code: string;
  start_date: string;
  end_date: string;
  progress_percent: number;
  status: string;
  basic_data_categories?: BasicDataCategory[];
}

interface BasicDataCategory {
  id: string;
  category_type: string;
  code: string;
  name: string;
}

interface Phase {
  id: string;
  project_id: string;
  name: string;
  start_date: string;
  end_date: string;
  progress_percent: number;
}

interface Task {
  id: string;
  project_id: string;
  name: string;
  start_date: string;
  due_date: string;
  progress_percent: number;
  status: string;
}

interface Milestone {
  id: string;
  project_id: string;
  name: string;
  target_date: string;
  status: string;
}

interface GanttTask {
  id: string;
  name: string;
  start: Date;
  end: Date;
  progress: number;
  status: string;
  type: 'project' | 'phase' | 'task' | 'milestone';
  projectName?: string;
}

interface ApplicationDomain {
  id: string;
  code: string;
  name: string;
  sort_order?: number;
}

export default function ProjectSchedulePage() {
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('project_id');

  const [projects, setProjects] = useState<Project[]>([]);
  const [phases, setPhases] = useState<Phase[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [applicationDomains, setApplicationDomains] = useState<ApplicationDomain[]>([]);
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'all' | 'project' | 'phase' | 'task'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApplicationDomains();
    fetchData();
  }, [selectedProject, selectedCategory]);

  // 获取应用领域分类
  const fetchApplicationDomains = async () => {
    try {
      const data = await apiGatewayClient.get<{ items: ApplicationDomain[] }>(
        '/api/v1/basic-data/categories?category_type=application_domain&limit=1000'
      );

      const items = data.items || [];

      // 过滤掉非活跃的分类
      const activeDomains = items.filter((cat: any) => cat.is_active !== false);

      // 可选：如果确实需要过滤特定的 code 前缀，可以取消注释下面的代码
      // const allowedCodes = ['01-', '02-', '03-', '04-', '05-', '06-', '07-', '08-', '09-', '10-', '11-', '12-', '99-'];
      // const filteredDomains = activeDomains.filter((cat: any) => {
      //   if (!cat.code) return false;
      //   return allowedCodes.some((code) => cat.code.startsWith(code));
      // });

      // 按 sort_order 排序，如果没有则按 code 排序
      const sortedDomains = activeDomains.sort((a: ApplicationDomain, b: ApplicationDomain) => {
        if (a.sort_order !== undefined && b.sort_order !== undefined) {
          return (a.sort_order || 0) - (b.sort_order || 0);
        }
        const aCode = a.code || '';
        const bCode = b.code || '';
        return aCode.localeCompare(bCode);
      });

      setApplicationDomains(sortedDomains);
    } catch (error: any) {
      console.error('获取应用领域分类失败:', error);
      // 静默处理错误，避免影响页面加载
      // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
      if (error?.statusCode !== 401) {
        // 只在非认证错误时记录
        console.warn('无法加载项目分类，将显示所有项目');
      }
      setApplicationDomains([]);
    }
  };

  // 获取项目的应用领域分类
  const getProjectApplicationDomain = (project: Project): string | null => {
    if (!project.basic_data_categories || project.basic_data_categories.length === 0) {
      return null;
    }
    const domainCategory = project.basic_data_categories.find(
      (cat) => cat.category_type === 'application_domain'
    );
    return domainCategory ? domainCategory.name : null;
  };

  // 根据分类过滤项目
  const filteredProjects = useMemo(() => {
    if (selectedCategory === 'all') {
      return projects;
    }
    return projects.filter((project) => {
      const domain = getProjectApplicationDomain(project);
      return domain === selectedCategory;
    });
  }, [projects, selectedCategory]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 并行获取所有数据
      const [projectsRes, phasesRes, tasksRes, milestonesRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/projects?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(
          `${apiUrl}/api/v1/project-phases${selectedProject !== 'all' ? `?project_id=${selectedProject}` : ''}`,
          { headers: { Authorization: `Bearer ${token}` } }
        ),
        fetch(
          `${apiUrl}/api/v1/tasks${selectedProject !== 'all' ? `?project_id=${selectedProject}` : ''}`,
          { headers: { Authorization: `Bearer ${token}` } }
        ),
        fetch(
          `${apiUrl}/api/v1/milestones${selectedProject !== 'all' ? `?project_id=${selectedProject}` : ''}`,
          { headers: { Authorization: `Bearer ${token}` } }
        ),
      ]);

      if (projectsRes.ok) {
        const data = await projectsRes.json();
        setProjects(data.items || []);
      }

      if (phasesRes.ok) {
        const data = await phasesRes.json();
        setPhases(data.items || []);
      }

      if (tasksRes.ok) {
        const data = await tasksRes.json();
        setTasks(data.items || []);
      }

      if (milestonesRes.ok) {
        const data = await milestonesRes.json();
        setMilestones(data.items || []);
      }
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 转换为甘特图任务
  const convertToGanttTasks = (): GanttTask[] => {
    const ganttTasks: GanttTask[] = [];
    const projectsToUse = selectedProject === 'all' ? filteredProjects : filteredProjects.filter((p) => p.id === selectedProject);

    // 添加项目
    if (viewMode === 'all' || viewMode === 'project') {
      projectsToUse.forEach((project) => {
        if (project.start_date && project.end_date) {
          ganttTasks.push({
            id: `project-${project.id}`,
            name: project.name,
            start: new Date(project.start_date),
            end: new Date(project.end_date),
            progress: project.progress_percent || 0,
            status: project.status,
            type: 'project',
          });
        }
      });
    }

    // 添加阶段
    if (viewMode === 'all' || viewMode === 'phase') {
      phases.forEach((phase) => {
        const project = projectsToUse.find((p) => p.id === phase.project_id);
        if (project && phase.start_date && phase.end_date) {
          ganttTasks.push({
            id: `phase-${phase.id}`,
            name: `${project.name} - ${phase.name}`,
            start: new Date(phase.start_date),
            end: new Date(phase.end_date),
            progress: phase.progress_percent || 0,
            status: 'active',
            type: 'phase',
            projectName: project.name,
          });
        }
      });
    }

    // 添加任务
    if (viewMode === 'all' || viewMode === 'task') {
      tasks.forEach((task) => {
        const project = projectsToUse.find((p) => p.id === task.project_id);
        if (project && task.start_date && task.due_date) {
          ganttTasks.push({
            id: `task-${task.id}`,
            name: `${project.name} - ${task.name}`,
            start: new Date(task.start_date),
            end: new Date(task.due_date),
            progress: task.progress_percent || 0,
            status: task.status,
            type: 'task',
            projectName: project.name,
          });
        }
      });
    }

    // 添加里程碑
    if (viewMode === 'all') {
      milestones.forEach((milestone) => {
        const project = projectsToUse.find((p) => p.id === milestone.project_id);
        if (project && milestone.target_date) {
          const targetDate = new Date(milestone.target_date);
          ganttTasks.push({
            id: `milestone-${milestone.id}`,
            name: `${project.name} - ${milestone.name}`,
            start: targetDate,
            end: new Date(targetDate.getTime() + 24 * 60 * 60 * 1000),
            progress: milestone.status === 'achieved' ? 100 : 0,
            status: milestone.status,
            type: 'milestone',
            projectName: project.name,
          });
        }
      });
    }

    // 按开始日期排序
    return ganttTasks.sort((a, b) => a.start.getTime() - b.start.getTime());
  };

  const ganttTasks = convertToGanttTasks();

  // 计算日期范围
  const allDates = ganttTasks.flatMap((t) => [t.start, t.end]);
  const minDate =
    allDates.length > 0 ? new Date(Math.min(...allDates.map((d) => d.getTime()))) : new Date();
  const maxDate =
    allDates.length > 0
      ? new Date(Math.max(...allDates.map((d) => d.getTime())))
      : new Date(Date.now() + 90 * 24 * 60 * 60 * 1000);

  // 计算统计数据（基于过滤后的项目）
  const stats = useMemo(() => {
    const filteredProjectIds = new Set(filteredProjects.map((p) => p.id));
    const filteredPhases = phases.filter((p) => filteredProjectIds.has(p.project_id));
    const filteredTasks = tasks.filter((t) => filteredProjectIds.has(t.project_id));
    const filteredMilestones = milestones.filter((m) => filteredProjectIds.has(m.project_id));

    return {
      totalProjects: filteredProjects.length,
      totalPhases: filteredPhases.length,
      totalTasks: filteredTasks.length,
      totalMilestones: filteredMilestones.length,
    };
  }, [filteredProjects, phases, tasks, milestones]);

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl shadow-xl border-2 border-blue-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500 rounded-xl shadow-lg">
              <Calendar className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">项目进度计划</h1>
              <p className="text-gray-600 mt-1">甘特图视图 - 项目、阶段、任务和里程碑的时间线</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="px-5 py-2.5 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 flex items-center gap-2 font-semibold shadow-md hover:shadow-lg">
              <Download className="h-5 w-5" />
              导出
            </button>
          </div>
        </div>
      </div>

      {/* 统计卡片 - 移到筛选条件上面 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl shadow-lg border-2 border-gray-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-gray-400 to-gray-500 rounded-xl shadow-md">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <div className="text-sm font-semibold text-gray-600 mb-1">总项目数</div>
          <div className="text-4xl font-bold text-gray-900">{stats.totalProjects}</div>
        </div>
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl shadow-lg border-2 border-blue-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-md">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <TrendingUp className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-sm font-semibold text-blue-700 mb-1">阶段数</div>
          <div className="text-4xl font-bold text-blue-600">{stats.totalPhases}</div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl shadow-lg border-2 border-green-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-md">
              <CheckCircle className="w-6 h-6 text-white" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <div className="text-sm font-semibold text-green-700 mb-1">任务数</div>
          <div className="text-4xl font-bold text-green-600">{stats.totalTasks}</div>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl shadow-lg border-2 border-purple-200 p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200">
          <div className="flex items-center justify-between mb-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-md">
              <Target className="w-6 h-6 text-white" />
            </div>
            <TrendingUp className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-sm font-semibold text-purple-700 mb-1">里程碑数</div>
          <div className="text-4xl font-bold text-purple-600">{stats.totalMilestones}</div>
        </div>
      </div>

      {/* 筛选条件 */}
      <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-6">
        <div className="flex items-center gap-2 text-gray-700 font-bold mb-5">
          <div className="p-1.5 bg-blue-100 rounded-lg">
            <Filter className="w-5 h-5 text-blue-600" />
          </div>
          <span className="text-lg">筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* 项目分类筛选 */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">项目分类</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
            >
              <option value="all">全部</option>
              {applicationDomains.map((domain) => (
                <option key={domain.id} value={domain.name}>
                  {domain.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">项目</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
            >
              <option value="all">所有项目</option>
              {filteredProjects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">视图模式</label>
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as any)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
            >
              <option value="all">全部（项目+阶段+任务+里程碑）</option>
              <option value="project">仅项目</option>
              <option value="phase">仅阶段</option>
              <option value="task">仅任务</option>
            </select>
          </div>
        </div>
      </div>

      {/* 甘特图 */}
      {loading ? (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : ganttTasks.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 mb-4">
            <Calendar className="h-10 w-10 text-gray-400" />
          </div>
          <p className="text-gray-600 font-semibold text-lg mb-2">暂无进度数据</p>
          <p className="text-sm text-gray-500">请先创建项目、阶段或任务</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-6">
          <GanttChart
            tasks={ganttTasks}
            startDate={minDate}
            endDate={maxDate}
            height={Math.max(400, ganttTasks.length * 50 + 100)}
          />
        </div>
      )}
    </div>
  );
}

