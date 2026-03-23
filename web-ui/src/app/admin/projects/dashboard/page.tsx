'use client';

import { useState, useEffect } from 'react';
import { getAccessToken } from '@/lib/auth';
import {
  FolderKanban,
  CheckCircle,
  Clock,
  AlertCircle,
  Target,
  TrendingUp,
  Calendar,
  FileText,
  Activity,
} from 'lucide-react';
import Link from 'next/link';
import ProjectPhaseProgress from '@/components/ProjectPhaseProgress';

interface DashboardStats {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  totalTasks: number;
  completedTasks: number;
  totalMilestones: number;
  completedMilestones: number;
  totalPhases: number;
  totalRisks: number;
  totalWeeklyReports: number;
  averageProgress: number;
}

interface BasicDataCategory {
  id: string;
  category_type: string;
  code: string;
  name: string;
}

interface Project {
  id: string;
  name: string;
  status: string;
  progress_percent: number;
  basic_data_categories?: BasicDataCategory[];
}

export default function ProjectDashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    activeProjects: 0,
    completedProjects: 0,
    totalTasks: 0,
    completedTasks: 0,
    totalMilestones: 0,
    completedMilestones: 0,
    totalPhases: 0,
    totalRisks: 0,
    totalWeeklyReports: 0,
    averageProgress: 0,
  });
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 并行获取所有数据
      const [projectsRes, tasksRes, milestonesRes, phasesRes, risksRes, weeklyReportsRes] =
        await Promise.all([
          fetch(`${apiUrl}/api/v1/projects`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiUrl}/api/v1/tasks`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiUrl}/api/v1/milestones`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiUrl}/api/v1/project-phases`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiUrl}/api/v1/risks`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiUrl}/api/v1/weekly-reports`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

      const projects = projectsRes.ok ? (await projectsRes.json()).items || [] : [];
      const tasks = tasksRes.ok ? (await tasksRes.json()).items || [] : [];
      const milestones = milestonesRes.ok ? (await milestonesRes.json()).items || [] : [];
      const phases = phasesRes.ok ? (await phasesRes.json()).items || [] : [];
      const risks = risksRes.ok ? (await risksRes.json()).items || [] : [];
      const weeklyReports = weeklyReportsRes.ok ? (await weeklyReportsRes.json()).items || [] : [];

      // 计算统计信息
      const activeProjects = projects.filter((p: Project) => p.status === 'active').length;
      const completedProjects = projects.filter((p: Project) => p.status === 'completed').length;
      const completedTasks = tasks.filter((t: any) => t.status === 'completed').length;
      const completedMilestones = milestones.filter(
        (m: any) => m.status === 'achieved' || m.status === 'completed'
      ).length;
      const averageProgress =
        projects.length > 0
          ? projects.reduce((sum: number, p: Project) => sum + (p.progress_percent || 0), 0) /
            projects.length
          : 0;

      setStats({
        totalProjects: projects.length,
        activeProjects,
        completedProjects,
        totalTasks: tasks.length,
        completedTasks,
        totalMilestones: milestones.length,
        completedMilestones,
        totalPhases: phases.length,
        totalRisks: risks.length,
        totalWeeklyReports: weeklyReports.length,
        averageProgress,
      });

      // 获取最近的项目
      setRecentProjects(projects.slice(0, 5));
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({
    title,
    value,
    icon: Icon,
    color,
    href,
  }: {
    title: string;
    value: number | string;
    icon: any;
    color: string;
    href?: string;
  }) => {
    const content = (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6 hover:shadow-lg transition-shadow">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">{title}</p>
            <p className="text-3xl font-bold" style={{ color }}>
              {value}
            </p>
          </div>
          <div className="p-3 rounded-lg" style={{ backgroundColor: `${color}20` }}>
            <Icon className="w-8 h-8" style={{ color }} />
          </div>
        </div>
      </div>
    );

    if (href) {
      return <Link href={href}>{content}</Link>;
    }
    return content;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">项目管理仪表盘</h1>
        <p className="text-gray-600 mt-1">项目整体概览和统计信息</p>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center text-gray-500">
          加载中...
        </div>
      ) : (
        <>
          {/* 核心指标 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="项目总数"
              value={stats.totalProjects}
              icon={FolderKanban}
              color="#3b82f6"
              href="/admin/projects"
            />
            <StatCard
              title="进行中项目"
              value={stats.activeProjects}
              icon={Activity}
              color="#10b981"
              href="/admin/projects"
            />
            <StatCard
              title="已完成项目"
              value={stats.completedProjects}
              icon={CheckCircle}
              color="#059669"
              href="/admin/projects"
            />
            <StatCard
              title="平均进度"
              value={`${stats.averageProgress.toFixed(1)}%`}
              icon={TrendingUp}
              color="#f59e0b"
            />
          </div>

          {/* 详细统计 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="任务总数"
              value={stats.totalTasks}
              icon={CheckCircle}
              color="#6366f1"
              href="/admin/projects/tasks"
            />
            <StatCard
              title="已完成任务"
              value={stats.completedTasks}
              icon={CheckCircle}
              color="#10b981"
              href="/admin/projects/tasks"
            />
            <StatCard
              title="里程碑"
              value={stats.totalMilestones}
              icon={Target}
              color="#8b5cf6"
              href="/admin/projects/milestones"
            />
            <StatCard
              title="项目阶段"
              value={stats.totalPhases}
              icon={Calendar}
              color="#ec4899"
              href="/admin/projects/phases"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <StatCard
              title="周报数量"
              value={stats.totalWeeklyReports}
              icon={FileText}
              color="#06b6d4"
              href="/admin/projects/weekly-reports"
            />
            <StatCard
              title="风险数量"
              value={stats.totalRisks}
              icon={AlertCircle}
              color="#ef4444"
              href="/admin/projects/risks"
            />
          </div>

          {/* 最近项目 */}
          {recentProjects.length > 0 && (
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">最近项目</h2>
                <Link href="/admin/projects" className="text-sm text-blue-600 hover:text-blue-800">
                  查看全部 →
                </Link>
              </div>
              <div className="space-y-3">
                {recentProjects.map((project) => (
                  <Link
                    key={project.id}
                    href={`/admin/projects/${project.id}`}
                    className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{project.name}</h3>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span
                            className={`px-2 py-1 rounded text-xs ${
                              project.status === 'active'
                                ? 'bg-blue-100 text-blue-700'
                                : project.status === 'completed'
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {project.status === 'active'
                              ? '进行中'
                              : project.status === 'completed'
                                ? '已完成'
                                : project.status === 'planning'
                                  ? '规划中'
                                  : project.status}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4 min-w-[300px]">
                        <div className="text-sm text-gray-600 mb-2">项目阶段</div>
                        <ProjectPhaseProgress
                          currentPhase={(() => {
                            // 从项目分类中获取项目阶段
                            if (
                              project.basic_data_categories &&
                              project.basic_data_categories.length > 0
                            ) {
                              const phaseCategory = project.basic_data_categories.find(
                                (cat) => cat.category_type === 'project_phase'
                              );
                              if (phaseCategory) {
                                // 优先使用ID，如果没有ID则使用code或name
                                return phaseCategory.id || phaseCategory.code || phaseCategory.name;
                              }
                            }
                            return undefined;
                          })()}
                          className="py-1"
                        />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* 快速操作 */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">快速操作</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link
                href="/admin/projects/create"
                className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <FolderKanban className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium">新建项目</span>
              </Link>
              <Link
                href="/admin/projects/import"
                className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <FileText className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium">导入Excel</span>
              </Link>
              <Link
                href="/admin/projects/tasks"
                className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <CheckCircle className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-medium">任务管理</span>
              </Link>
              <Link
                href="/admin/projects/weekly-reports"
                className="flex items-center gap-2 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Calendar className="w-5 h-5 text-orange-600" />
                <span className="text-sm font-medium">周报管理</span>
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
