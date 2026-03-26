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
  Building2,
  Users,
  DollarSign,
  Heart,
  BarChart3,
  PieChart,
  ArrowRight,
  Zap,
  Shield,
  Award,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import Link from 'next/link';
import ProjectPhaseProgress from '@/components/ProjectPhaseProgress';
import ErrorMessage from '@/components/ErrorMessage';

interface DashboardStats {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  planningProjects: number;
  delayedProjects: number;
  totalTasks: number;
  completedTasks: number;
  pendingTasks: number;
  inProgressTasks: number;
  totalMilestones: number;
  completedMilestones: number;
  totalPhases: number;
  totalRisks: number;
  highRisks: number;
  totalWeeklyReports: number;
  totalPrograms: number;
  activePrograms: number;
  averageProgress: number;
  averageHealthScore: number;
  totalBudget: number;
  totalActualCost: number;
}

interface Project {
  id: string;
  name: string;
  status: string;
  progress_percent: number;
  health_score: number;
  budget?: number;
  actual_cost?: number;
  manager_name?: string;
  start_date?: string;
  end_date?: string;
  basic_data_categories?: any[];
}

interface Program {
  id: string;
  name: string;
  status: string;
  progress_percent: number;
  health_score: number;
  project_count: number;
}

export default function ProjectDashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    activeProjects: 0,
    completedProjects: 0,
    planningProjects: 0,
    delayedProjects: 0,
    totalTasks: 0,
    completedTasks: 0,
    pendingTasks: 0,
    inProgressTasks: 0,
    totalMilestones: 0,
    completedMilestones: 0,
    totalPhases: 0,
    totalRisks: 0,
    highRisks: 0,
    totalWeeklyReports: 0,
    totalPrograms: 0,
    activePrograms: 0,
    averageProgress: 0,
    averageHealthScore: 0,
    totalBudget: 0,
    totalActualCost: 0,
  });
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [topPrograms, setTopPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    fetchDashboardData();
    // 每5分钟自动刷新
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 并行获取所有数据
      const [
        projectsRes,
        tasksRes,
        milestonesRes,
        phasesRes,
        risksRes,
        weeklyReportsRes,
        programsRes,
      ] = await Promise.all([
        fetch(`${apiUrl}/api/v1/projects?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/tasks?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/milestones?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/project-phases?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/risks?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/weekly-reports?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/programs?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      const projects = projectsRes.ok ? (await projectsRes.json()).items || [] : [];
      const tasks = tasksRes.ok ? (await tasksRes.json()).items || [] : [];
      const milestones = milestonesRes.ok ? (await milestonesRes.json()).items || [] : [];
      const phases = phasesRes.ok ? (await phasesRes.json()).items || [] : [];
      const risks = risksRes.ok ? (await risksRes.json()).items || [] : [];
      const weeklyReports = weeklyReportsRes.ok ? (await weeklyReportsRes.json()).items || [] : [];
      const programs = programsRes.ok ? (await programsRes.json()).items || [] : [];

      // 计算统计信息
      const activeProjects = projects.filter((p: Project) => p.status === 'active').length;
      const completedProjects = projects.filter((p: Project) => p.status === 'completed').length;
      const planningProjects = projects.filter((p: Project) => p.status === 'planning').length;
      const delayedProjects = projects.filter((p: Project) => p.status === 'delayed').length;

      const completedTasks = tasks.filter((t: any) => t.status === 'completed').length;
      const pendingTasks = tasks.filter((t: any) => t.status === 'pending').length;
      const inProgressTasks = tasks.filter((t: any) => t.status === 'in_progress').length;

      const completedMilestones = milestones.filter(
        (m: any) => m.status === 'achieved' || m.status === 'completed'
      ).length;

      const highRisks = risks.filter((r: any) => r.severity === 'high' || r.level === 'high').length;

      const activePrograms = programs.filter((p: Program) => p.status === 'active').length;

      const averageProgress =
        projects.length > 0
          ? projects.reduce((sum: number, p: Project) => sum + (p.progress_percent || 0), 0) /
            projects.length
          : 0;
      
      const averageHealthScore =
        projects.length > 0
          ? projects.reduce((sum: number, p: Project) => sum + (p.health_score || 0), 0) /
            projects.length
          : 0;
      
      const totalBudget = projects.reduce((sum: number, p: Project) => sum + (p.budget || 0), 0);
      const totalActualCost = projects.reduce((sum: number, p: Project) => sum + (p.actual_cost || 0), 0);

      setStats({
        totalProjects: projects.length,
        activeProjects,
        completedProjects,
        planningProjects,
        delayedProjects,
        totalTasks: tasks.length,
        completedTasks,
        pendingTasks,
        inProgressTasks,
        totalMilestones: milestones.length,
        completedMilestones,
        totalPhases: phases.length,
        totalRisks: risks.length,
        highRisks,
        totalWeeklyReports: weeklyReports.length,
        totalPrograms: programs.length,
        activePrograms,
        averageProgress,
        averageHealthScore,
        totalBudget,
        totalActualCost,
      });

      // 获取最近的项目（按更新时间排序）
      const sortedProjects = [...projects]
        .sort((a: Project, b: Project) => {
          const aTime = new Date(a.updated_at || a.created_at || 0).getTime();
          const bTime = new Date(b.updated_at || b.created_at || 0).getTime();
          return bTime - aTime;
        })
        .slice(0, 5);
      setRecentProjects(sortedProjects);

      // 获取项目群（按项目数量排序）
      const sortedPrograms = [...programs]
        .sort((a: Program, b: Program) => (b.project_count || 0) - (a.project_count || 0))
        .slice(0, 5);
      setTopPrograms(sortedPrograms);

      setLastUpdated(new Date());
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
      setError('获取仪表盘数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({
    title,
    value,
    icon: Icon,
    gradient,
    href,
    subtitle,
    trend,
  }: {
    title: string;
    value: number | string;
    icon: any;
    gradient: string;
    href?: string;
    subtitle?: string;
    trend?: { value: number; label: string };
  }) => {
    const content = (
      <div
        className={`relative overflow-hidden rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-[1.02] ${gradient} p-6 text-white`}
      >
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
              <Icon className="w-6 h-6" />
            </div>
            {trend && (
              <div className="text-right">
                <div className="text-sm opacity-90">{trend.label}</div>
                <div className="text-lg font-bold">{trend.value > 0 ? '+' : ''}{trend.value}%</div>
              </div>
            )}
          </div>
          <div>
            <p className="text-sm opacity-90 mb-1">{title}</p>
            <p className="text-4xl font-bold mb-1">{value}</p>
            {subtitle && <p className="text-sm opacity-75">{subtitle}</p>}
          </div>
        </div>
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full -ml-12 -mb-12"></div>
      </div>
    );

    if (href) {
      return <Link href={href}>{content}</Link>;
    }
    return content;
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'from-green-500 to-emerald-600';
    if (score >= 60) return 'from-yellow-500 to-orange-600';
    if (score >= 40) return 'from-orange-500 to-red-600';
    return 'from-red-500 to-rose-600';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'planning':
        return 'bg-gray-500';
      case 'delayed':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'planning':
        return '规划中';
      case 'delayed':
        return '已延迟';
      default:
        return status;
    }
  };

  // 计算项目状态分布
  const statusDistribution = [
    { status: 'active', count: stats.activeProjects, label: '进行中', color: 'bg-blue-500' },
    { status: 'completed', count: stats.completedProjects, label: '已完成', color: 'bg-green-500' },
    { status: 'planning', count: stats.planningProjects, label: '规划中', color: 'bg-gray-500' },
    { status: 'delayed', count: stats.delayedProjects, label: '已延迟', color: 'bg-red-500' },
  ];

  const totalStatusCount = statusDistribution.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-xl border-2 border-indigo-200 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
              <BarChart3 className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">项目管理仪表盘</h1>
              <p className="text-gray-600 mt-1">项目整体概览和统计分析</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right text-sm text-gray-600">
              <div>最后更新</div>
              <div className="font-medium">
                {lastUpdated.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
            <button
              onClick={fetchDashboardData}
              disabled={loading}
              className="p-3 bg-white rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-50"
              title="刷新数据"
            >
              <RefreshCw className={`w-5 h-5 text-indigo-600 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}

      {loading ? (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-12 text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="text-gray-600 mt-4">加载中...</p>
        </div>
      ) : (
        <>
          {/* 核心指标 - 第一行 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="项目总数"
              value={stats.totalProjects}
              icon={FolderKanban}
              gradient="bg-gradient-to-br from-blue-500 to-cyan-600"
              href="/projects"
              subtitle={`${stats.activeProjects} 个进行中`}
            />
            <StatCard
              title="进行中项目"
              value={stats.activeProjects}
              icon={Activity}
              gradient="bg-gradient-to-br from-green-500 to-emerald-600"
              href="/projects"
              subtitle={`${stats.completedProjects} 个已完成`}
            />
            <StatCard
              title="平均进度"
              value={`${stats.averageProgress.toFixed(1)}%`}
              icon={TrendingUp}
              gradient="bg-gradient-to-br from-purple-500 to-pink-600"
              subtitle={`${stats.totalProjects} 个项目平均`}
            />
            <StatCard
              title="健康度评分"
              value={stats.averageHealthScore.toFixed(1)}
              icon={Heart}
              gradient={`bg-gradient-to-br ${getHealthScoreColor(stats.averageHealthScore)}`}
              subtitle={stats.averageHealthScore >= 80 ? '优秀' : stats.averageHealthScore >= 60 ? '良好' : '需关注'}
            />
          </div>

          {/* 核心指标 - 第二行 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="任务总数"
              value={stats.totalTasks}
              icon={CheckCircle}
              gradient="bg-gradient-to-br from-indigo-500 to-purple-600"
              href="/projects/tasks"
              subtitle={`${stats.completedTasks} 个已完成`}
            />
            <StatCard
              title="里程碑"
              value={stats.totalMilestones}
              icon={Target}
              gradient="bg-gradient-to-br from-violet-500 to-purple-600"
              href="/projects/milestones"
              subtitle={`${stats.completedMilestones} 个已完成`}
            />
            <StatCard
              title="项目群"
              value={stats.totalPrograms}
              icon={Building2}
              gradient="bg-gradient-to-br from-rose-500 to-pink-600"
              href="/projects/programs"
              subtitle={`${stats.activePrograms} 个活跃`}
            />
            <StatCard
              title="风险数量"
              value={stats.totalRisks}
              icon={AlertCircle}
              gradient="bg-gradient-to-br from-red-500 to-rose-600"
              href="/projects/risks"
              subtitle={`${stats.highRisks} 个高风险`}
            />
          </div>

          {/* 详细统计和图表 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 项目状态分布 */}
            <div className="lg:col-span-2 bg-white rounded-2xl shadow-xl border-2 border-gray-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 rounded-lg">
                    <PieChart className="w-6 h-6 text-indigo-600" />
                  </div>
                  <h2 className="text-xl font-bold text-gray-900">项目状态分布</h2>
                </div>
                <Link
                  href="/projects"
                  className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                >
                  查看全部 <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
              <div className="space-y-4">
                {statusDistribution.map((item) => {
                  const percentage = totalStatusCount > 0 ? (item.count / totalStatusCount) * 100 : 0;
                  return (
                    <div key={item.status} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                          <span className="font-medium text-gray-700">{item.label}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-gray-600">{item.count} 个</span>
                          <span className="text-gray-500 w-16 text-right">{percentage.toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${item.color} rounded-full transition-all duration-500`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 任务状态统计 */}
            <div className="bg-white rounded-2xl shadow-xl border-2 border-gray-100 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Activity className="w-6 h-6 text-green-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">任务状态</h2>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-gray-700">已完成</span>
                  </div>
                  <span className="text-2xl font-bold text-green-600">{stats.completedTasks}</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-blue-50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <Clock className="w-5 h-5 text-blue-600" />
                    <span className="font-medium text-gray-700">进行中</span>
                  </div>
                  <span className="text-2xl font-bold text-blue-600">{stats.inProgressTasks}</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-gray-600" />
                    <span className="font-medium text-gray-700">待处理</span>
                  </div>
                  <span className="text-2xl font-bold text-gray-600">{stats.pendingTasks}</span>
                </div>
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">总计</span>
                    <span className="text-lg font-bold text-gray-900">{stats.totalTasks}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 预算和成本 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl shadow-xl border-2 border-gray-100 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <DollarSign className="w-6 h-6 text-yellow-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">预算统计</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">总预算</span>
                    <span className="text-2xl font-bold text-gray-900">
                      ¥{stats.totalBudget.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">实际成本</span>
                    <span className="text-2xl font-bold text-indigo-600">
                      ¥{stats.totalActualCost.toLocaleString('zh-CN', { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                  {stats.totalBudget > 0 && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600">预算使用率</span>
                        <span className="text-sm font-medium text-gray-700">
                          {((stats.totalActualCost / stats.totalBudget) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            (stats.totalActualCost / stats.totalBudget) * 100 > 100
                              ? 'bg-gradient-to-r from-red-500 to-rose-600'
                              : (stats.totalActualCost / stats.totalBudget) * 100 > 80
                                ? 'bg-gradient-to-r from-yellow-500 to-orange-600'
                                : 'bg-gradient-to-r from-green-500 to-emerald-600'
                          }`}
                          style={{
                            width: `${Math.min((stats.totalActualCost / stats.totalBudget) * 100, 100)}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-xl border-2 border-gray-100 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Award className="w-6 h-6 text-purple-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">其他统计</h2>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-xl">
                  <div className="text-sm text-gray-600 mb-1">项目阶段</div>
                  <div className="text-3xl font-bold text-blue-600">{stats.totalPhases}</div>
                </div>
                <div className="p-4 bg-green-50 rounded-xl">
                  <div className="text-sm text-gray-600 mb-1">周报数量</div>
                  <div className="text-3xl font-bold text-green-600">{stats.totalWeeklyReports}</div>
                </div>
                <div className="p-4 bg-orange-50 rounded-xl">
                  <div className="text-sm text-gray-600 mb-1">高风险</div>
                  <div className="text-3xl font-bold text-orange-600">{stats.highRisks}</div>
                </div>
                <div className="p-4 bg-purple-50 rounded-xl">
                  <div className="text-sm text-gray-600 mb-1">活跃项目群</div>
                  <div className="text-3xl font-bold text-purple-600">{stats.activePrograms}</div>
                </div>
              </div>
            </div>
          </div>

          {/* 最近项目和项目群 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 最近项目 */}
            {recentProjects.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl border-2 border-gray-100 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 rounded-lg">
                      <FolderKanban className="w-6 h-6 text-indigo-600" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900">最近项目</h2>
                  </div>
                  <Link
                    href="/projects"
                    className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  >
                    查看全部 <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
                <div className="space-y-3">
                  {recentProjects.map((project) => (
                    <Link
                      key={project.id}
                      href={`/projects/${project.id}`}
                      className="block p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl hover:from-indigo-50 hover:to-purple-50 transition-all border border-gray-200 hover:border-indigo-300 hover:shadow-md"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate mb-2">{project.name}</h3>
                          <div className="flex items-center gap-3 text-sm">
                            <span
                              className={`px-2 py-1 rounded-lg text-xs font-medium ${getStatusColor(project.status)} text-white`}
                            >
                              {getStatusText(project.status)}
                            </span>
                            {project.manager_name && (
                              <span className="text-gray-600 flex items-center gap-1">
                                <Users className="w-4 h-4" />
                                {project.manager_name}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="ml-4 text-right">
                          <div className="text-sm text-gray-600 mb-1">进度</div>
                          <div className="text-2xl font-bold text-indigo-600">
                            {project.progress_percent.toFixed(0)}%
                          </div>
                          <div className="w-24 h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all"
                              style={{ width: `${project.progress_percent}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* 项目群 */}
            {topPrograms.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl border-2 border-gray-100 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-rose-100 rounded-lg">
                      <Building2 className="w-6 h-6 text-rose-600" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-900">项目群</h2>
                  </div>
                  <Link
                    href="/projects/programs"
                    className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  >
                    查看全部 <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
                <div className="space-y-3">
                  {topPrograms.map((program) => (
                    <Link
                      key={program.id}
                      href={`/projects/programs/${program.id}`}
                      className="block p-4 bg-gradient-to-r from-rose-50 to-pink-50 rounded-xl hover:from-rose-100 hover:to-pink-100 transition-all border border-rose-200 hover:border-rose-300 hover:shadow-md"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate mb-2">{program.name}</h3>
                          <div className="flex items-center gap-3 text-sm">
                            <span
                              className={`px-2 py-1 rounded-lg text-xs font-medium ${
                                program.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                              } text-white`}
                            >
                              {program.status === 'active' ? '活跃' : program.status}
                            </span>
                            <span className="text-gray-600 flex items-center gap-1">
                              <FolderKanban className="w-4 h-4" />
                              {program.project_count} 个项目
                            </span>
                          </div>
                        </div>
                        <div className="ml-4 text-right">
                          <div className="text-sm text-gray-600 mb-1">进度</div>
                          <div className="text-2xl font-bold text-rose-600">
                            {program.progress_percent.toFixed(0)}%
                          </div>
                          <div className="w-24 h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-rose-500 to-pink-600 rounded-full transition-all"
                              style={{ width: `${program.progress_percent}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 快速操作 */}
          <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-xl border-2 border-indigo-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-indigo-500 rounded-lg">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">快速操作</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link
                href="/projects/create"
                className="flex flex-col items-center gap-3 p-6 bg-white rounded-xl hover:shadow-lg transition-all border-2 border-gray-200 hover:border-indigo-300 group"
              >
                <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl group-hover:scale-110 transition-transform">
                  <FolderKanban className="w-6 h-6 text-white" />
                </div>
                <span className="text-sm font-semibold text-gray-700 group-hover:text-indigo-600">新建项目</span>
              </Link>
              <Link
                href="/projects/programs/create"
                className="flex flex-col items-center gap-3 p-6 bg-white rounded-xl hover:shadow-lg transition-all border-2 border-gray-200 hover:border-rose-300 group"
              >
                <div className="p-3 bg-gradient-to-br from-rose-500 to-pink-600 rounded-xl group-hover:scale-110 transition-transform">
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                <span className="text-sm font-semibold text-gray-700 group-hover:text-rose-600">创建项目群</span>
              </Link>
              <Link
                href="/projects/tasks"
                className="flex flex-col items-center gap-3 p-6 bg-white rounded-xl hover:shadow-lg transition-all border-2 border-gray-200 hover:border-purple-300 group"
              >
                <div className="p-3 bg-gradient-to-br from-purple-500 to-violet-600 rounded-xl group-hover:scale-110 transition-transform">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <span className="text-sm font-semibold text-gray-700 group-hover:text-purple-600">任务管理</span>
              </Link>
              <Link
                href="/projects/weekly-reports"
                className="flex flex-col items-center gap-3 p-6 bg-white rounded-xl hover:shadow-lg transition-all border-2 border-gray-200 hover:border-orange-300 group"
              >
                <div className="p-3 bg-gradient-to-br from-orange-500 to-amber-600 rounded-xl group-hover:scale-110 transition-transform">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
                <span className="text-sm font-semibold text-gray-700 group-hover:text-orange-600">周报管理</span>
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
