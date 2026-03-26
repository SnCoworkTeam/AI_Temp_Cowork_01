'use client';

import { useState, useEffect } from 'react';
import { getAccessToken } from '@/lib/auth';
import {
  BarChart3,
  TrendingUp,
  Calendar,
  Target,
  CheckCircle2,
  Clock,
  AlertCircle,
  Filter,
  Download,
} from 'lucide-react';

interface Phase {
  id: string;
  project_id: string;
  project_name: string;
  name: string;
  sequence: number;
  start_date: string | null;
  end_date: string | null;
  progress_percent: number;
  created_at: string;
}

interface Project {
  id: string;
  name: string;
  project_code: string;
}

interface PhaseStatistics {
  totalPhases: number;
  completedPhases: number;
  inProgressPhases: number;
  notStartedPhases: number;
  averageProgress: number;
  onTimePhases: number;
  delayedPhases: number;
  phasesByProject: Record<string, number>;
  progressDistribution: {
    range: string;
    count: number;
  }[];
}

export default function PhaseStatisticsPage() {
  const [phases, setPhases] = useState<Phase[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [statistics, setStatistics] = useState<PhaseStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState<string>('all');
  const [dateRange, setDateRange] = useState<'all' | 'week' | 'month' | 'quarter'>('all');

  useEffect(() => {
    fetchProjects();
    fetchPhases();
  }, [selectedProject]);

  useEffect(() => {
    if (phases.length > 0) {
      calculateStatistics();
    }
  }, [phases, dateRange]);

  const fetchProjects = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      const response = await fetch(`${apiUrl}/api/v1/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data.items || []);
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
    }
  };

  const fetchPhases = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      let url = `${apiUrl}/api/v1/project-phases`;
      if (selectedProject && selectedProject !== 'all') {
        url += `?project_id=${selectedProject}`;
      }
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setPhases(data.items || []);
      }
    } catch (error) {
      console.error('获取阶段列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStatistics = () => {
    const now = new Date();
    let filteredPhases = phases;

    // 按日期范围筛选
    if (dateRange !== 'all') {
      const rangeStart = new Date();
      switch (dateRange) {
        case 'week':
          rangeStart.setDate(now.getDate() - 7);
          break;
        case 'month':
          rangeStart.setMonth(now.getMonth() - 1);
          break;
        case 'quarter':
          rangeStart.setMonth(now.getMonth() - 3);
          break;
      }
      filteredPhases = phases.filter((phase) => {
        const phaseDate = phase.start_date ? new Date(phase.start_date) : null;
        return phaseDate && phaseDate >= rangeStart;
      });
    }

    const totalPhases = filteredPhases.length;
    const completedPhases = filteredPhases.filter((p) => p.progress_percent >= 100).length;
    const inProgressPhases = filteredPhases.filter(
      (p) => p.progress_percent > 0 && p.progress_percent < 100
    ).length;
    const notStartedPhases = filteredPhases.filter((p) => p.progress_percent === 0).length;
    const averageProgress =
      totalPhases > 0
        ? filteredPhases.reduce((sum, p) => sum + p.progress_percent, 0) / totalPhases
        : 0;

    // 计算按时/延期
    let onTimePhases = 0;
    let delayedPhases = 0;
    filteredPhases.forEach((phase) => {
      if (phase.end_date) {
        const endDate = new Date(phase.end_date);
        if (phase.progress_percent >= 100) {
          // 已完成，检查是否按时
          if (endDate >= now) {
            onTimePhases++;
          } else {
            delayedPhases++;
          }
        } else {
          // 未完成，检查是否已过期
          if (endDate < now) {
            delayedPhases++;
          } else {
            onTimePhases++;
          }
        }
      }
    });

    // 按项目分组统计
    const phasesByProject: Record<string, number> = {};
    filteredPhases.forEach((phase) => {
      const projectName = phase.project_name || '未知项目';
      phasesByProject[projectName] = (phasesByProject[projectName] || 0) + 1;
    });

    // 进度分布
    const progressDistribution = [
      { range: '0%', count: filteredPhases.filter((p) => p.progress_percent === 0).length },
      {
        range: '1-25%',
        count: filteredPhases.filter((p) => p.progress_percent > 0 && p.progress_percent <= 25)
          .length,
      },
      {
        range: '26-50%',
        count: filteredPhases.filter((p) => p.progress_percent > 25 && p.progress_percent <= 50)
          .length,
      },
      {
        range: '51-75%',
        count: filteredPhases.filter((p) => p.progress_percent > 50 && p.progress_percent <= 75)
          .length,
      },
      {
        range: '76-99%',
        count: filteredPhases.filter((p) => p.progress_percent > 75 && p.progress_percent < 100)
          .length,
      },
      { range: '100%', count: filteredPhases.filter((p) => p.progress_percent >= 100).length },
    ];

    setStatistics({
      totalPhases,
      completedPhases,
      inProgressPhases,
      notStartedPhases,
      averageProgress,
      onTimePhases,
      delayedPhases,
      phasesByProject,
      progressDistribution,
    });
  };

  const exportStatistics = () => {
    if (!statistics) return;

    const data = {
      统计时间: new Date().toLocaleString('zh-CN'),
      筛选项目:
        selectedProject === 'all'
          ? '所有项目'
          : projects.find((p) => p.id === selectedProject)?.name || selectedProject,
      日期范围:
        dateRange === 'all'
          ? '全部'
          : dateRange === 'week'
            ? '最近一周'
            : dateRange === 'month'
              ? '最近一月'
              : '最近一季度',
      总阶段数: statistics.totalPhases,
      已完成: statistics.completedPhases,
      进行中: statistics.inProgressPhases,
      未开始: statistics.notStartedPhases,
      平均进度: `${statistics.averageProgress.toFixed(1)}%`,
      按时完成: statistics.onTimePhases,
      延期: statistics.delayedPhases,
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `阶段统计_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">阶段统计</h1>
          <p className="text-gray-600 mt-1">项目阶段进度统计与分析</p>
        </div>
        <button
          onClick={exportStatistics}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          导出统计
        </button>
      </div>

      {/* 筛选条件 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-gray-700 font-medium mb-4">
          <Filter className="w-4 h-4" />
          <span>筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">项目筛选</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">所有项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name} ({project.project_code})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">日期范围</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value as any)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">全部</option>
              <option value="week">最近一周</option>
              <option value="month">最近一月</option>
              <option value="quarter">最近一季度</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center text-gray-500">
          加载中...
        </div>
      ) : !statistics ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center">
          <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">暂无统计数据</p>
        </div>
      ) : (
        <>
          {/* 核心指标卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-gray-600">总阶段数</div>
                <Target className="h-5 w-5 text-blue-500" />
              </div>
              <div className="text-3xl font-bold text-gray-900">{statistics.totalPhases}</div>
            </div>
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-gray-600">已完成</div>
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              </div>
              <div className="text-3xl font-bold text-green-600">{statistics.completedPhases}</div>
              <div className="text-xs text-gray-500 mt-1">
                {statistics.totalPhases > 0
                  ? ((statistics.completedPhases / statistics.totalPhases) * 100).toFixed(1)
                  : 0}
                %
              </div>
            </div>
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-gray-600">进行中</div>
                <Clock className="h-5 w-5 text-yellow-500" />
              </div>
              <div className="text-3xl font-bold text-yellow-600">
                {statistics.inProgressPhases}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {statistics.totalPhases > 0
                  ? ((statistics.inProgressPhases / statistics.totalPhases) * 100).toFixed(1)
                  : 0}
                %
              </div>
            </div>
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-gray-600">平均进度</div>
                <TrendingUp className="h-5 w-5 text-blue-500" />
              </div>
              <div className="text-3xl font-bold text-blue-600">
                {statistics.averageProgress.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* 状态分布 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">阶段状态分布</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">已完成</span>
                    <span className="font-medium">{statistics.completedPhases}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
                      style={{
                        width: `${statistics.totalPhases > 0 ? (statistics.completedPhases / statistics.totalPhases) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">进行中</span>
                    <span className="font-medium">{statistics.inProgressPhases}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-500 h-2 rounded-full transition-all"
                      style={{
                        width: `${statistics.totalPhases > 0 ? (statistics.inProgressPhases / statistics.totalPhases) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">未开始</span>
                    <span className="font-medium">{statistics.notStartedPhases}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gray-400 h-2 rounded-full transition-all"
                      style={{
                        width: `${statistics.totalPhases > 0 ? (statistics.notStartedPhases / statistics.totalPhases) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">时间管理</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    <span className="text-gray-700">按时完成</span>
                  </div>
                  <span className="text-2xl font-bold text-green-600">
                    {statistics.onTimePhases}
                  </span>
                </div>
                <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    <span className="text-gray-700">延期</span>
                  </div>
                  <span className="text-2xl font-bold text-red-600">
                    {statistics.delayedPhases}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 进度分布 */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">进度分布</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {statistics.progressDistribution.map((item, index) => (
                <div key={index} className="text-center">
                  <div className="text-2xl font-bold text-gray-900 mb-1">{item.count}</div>
                  <div className="text-sm text-gray-600">{item.range}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 项目阶段分布 */}
          {Object.keys(statistics.phasesByProject).length > 0 && (
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">各项目阶段数量</h3>
              <div className="space-y-3">
                {Object.entries(statistics.phasesByProject)
                  .sort(([, a], [, b]) => b - a)
                  .map(([projectName, count]) => (
                    <div key={projectName}>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-700 truncate">{projectName}</span>
                        <span className="font-medium text-gray-900">{count}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{
                            width: `${statistics.totalPhases > 0 ? (count / statistics.totalPhases) * 100 : 0}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
