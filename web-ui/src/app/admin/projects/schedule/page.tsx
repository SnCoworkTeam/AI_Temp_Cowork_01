'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { GanttChart } from '@/components/charts/GanttChart';
import { Calendar, Filter, Download } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  project_code: string;
  start_date: string;
  end_date: string;
  progress_percent: number;
  status: string;
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

export default function ProjectSchedulePage() {
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('project_id');

  const [projects, setProjects] = useState<Project[]>([]);
  const [phases, setPhases] = useState<Phase[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');
  const [viewMode, setViewMode] = useState<'all' | 'project' | 'phase' | 'task'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [selectedProject]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 并行获取所有数据
      const [projectsRes, phasesRes, tasksRes, milestonesRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/projects`, {
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

    // 添加项目
    if (viewMode === 'all' || viewMode === 'project') {
      projects.forEach((project) => {
        if (selectedProject === 'all' || project.id === selectedProject) {
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
        }
      });
    }

    // 添加阶段
    if (viewMode === 'all' || viewMode === 'phase') {
      phases.forEach((phase) => {
        if (selectedProject === 'all' || phase.project_id === selectedProject) {
          if (phase.start_date && phase.end_date) {
            const project = projects.find((p) => p.id === phase.project_id);
            ganttTasks.push({
              id: `phase-${phase.id}`,
              name: `${project?.name || ''} - ${phase.name}`,
              start: new Date(phase.start_date),
              end: new Date(phase.end_date),
              progress: phase.progress_percent || 0,
              status: 'active',
              type: 'phase',
              projectName: project?.name,
            });
          }
        }
      });
    }

    // 添加任务
    if (viewMode === 'all' || viewMode === 'task') {
      tasks.forEach((task) => {
        if (selectedProject === 'all' || task.project_id === selectedProject) {
          if (task.start_date && task.due_date) {
            const project = projects.find((p) => p.id === task.project_id);
            ganttTasks.push({
              id: `task-${task.id}`,
              name: `${project?.name || ''} - ${task.name}`,
              start: new Date(task.start_date),
              end: new Date(task.due_date),
              progress: task.progress_percent || 0,
              status: task.status,
              type: 'task',
              projectName: project?.name,
            });
          }
        }
      });
    }

    // 添加里程碑
    if (viewMode === 'all') {
      milestones.forEach((milestone) => {
        if (selectedProject === 'all' || milestone.project_id === selectedProject) {
          if (milestone.target_date) {
            const project = projects.find((p) => p.id === milestone.project_id);
            const targetDate = new Date(milestone.target_date);
            ganttTasks.push({
              id: `milestone-${milestone.id}`,
              name: `${project?.name || ''} - ${milestone.name}`,
              start: targetDate,
              end: new Date(targetDate.getTime() + 24 * 60 * 60 * 1000), // 里程碑显示为1天
              progress: milestone.status === 'achieved' ? 100 : 0,
              status: milestone.status,
              type: 'milestone',
              projectName: project?.name,
            });
          }
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

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">项目进度计划</h1>
          <p className="text-gray-600 mt-1">甘特图视图 - 项目、阶段、任务和里程碑的时间线</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center gap-2">
            <Download className="h-4 w-4" />
            导出
          </button>
        </div>
      </div>

      {/* 过滤器 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-gray-700 font-medium mb-4">
          <Filter className="w-4 h-4" />
          <span>筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">项目</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">所有项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">视图模式</label>
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as any)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center text-gray-500">
          加载中...
        </div>
      ) : ganttTasks.length === 0 ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">暂无进度数据</p>
          <p className="text-sm text-gray-400">请先创建项目、阶段或任务</p>
        </div>
      ) : (
        <GanttChart
          tasks={ganttTasks}
          startDate={minDate}
          endDate={maxDate}
          height={Math.max(400, ganttTasks.length * 50 + 100)}
        />
      )}

      {/* 统计信息 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="text-sm text-gray-600">总项目数</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {projects.filter((p) => selectedProject === 'all' || p.id === selectedProject).length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="text-sm text-gray-600">阶段数</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {
              phases.filter((p) => selectedProject === 'all' || p.project_id === selectedProject)
                .length
            }
          </div>
        </div>
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="text-sm text-gray-600">任务数</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {
              tasks.filter((t) => selectedProject === 'all' || t.project_id === selectedProject)
                .length
            }
          </div>
        </div>
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="text-sm text-gray-600">里程碑数</div>
          <div className="text-2xl font-bold text-purple-600 mt-1">
            {
              milestones.filter(
                (m) => selectedProject === 'all' || m.project_id === selectedProject
              ).length
            }
          </div>
        </div>
      </div>
    </div>
  );
}
