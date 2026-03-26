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

interface PhaseCategory {
  id: string;
  name: string;
  code: string;
  category_type: string;
  sort_order?: number;
}

interface ProjectPhase {
  id: string;
  project_id: string;
  project_name: string;
  category_id: string;
  category_name?: string;
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
  phasesByCategory: Record<string, number>;
  phasesByProject: Record<string, number>;
  phasesByStage: Record<string, {
    count: number;
    completed: number;
    inProgress: number;
    notStarted: number;
    averageProgress: number;
  }>;
  progressDistribution: {
    range: string;
    count: number;
  }[];
}

export default function PhaseStatisticsPage() {
  const [phaseCategories, setPhaseCategories] = useState<PhaseCategory[]>([]);
  const [phases, setPhases] = useState<ProjectPhase[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [statistics, setStatistics] = useState<PhaseStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [dateRange, setDateRange] = useState<'all' | 'week' | 'month' | 'quarter'>('all');

  useEffect(() => {
    fetchPhaseCategories();
    fetchProjects();
  }, []);

  useEffect(() => {
    fetchPhases();
  }, [selectedProject]);

  useEffect(() => {
    if (phases.length > 0) {
      calculateStatistics();
    }
  }, [phases, dateRange, selectedCategory]);

  // 从基础数据获取项目阶段分类
  const fetchPhaseCategories = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      const response = await fetch(
        `${apiUrl}/api/v1/basic-data/categories?category_type=project_phase&limit=1000`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        const data = await response.json();
        const categories = (data.items || []).filter((cat: any) => cat.is_active !== false);
        // 按sort_order排序，如果没有sort_order则按code排序
        categories.sort((a: PhaseCategory, b: PhaseCategory) => {
          if (a.sort_order !== b.sort_order) {
            return (a.sort_order || 0) - (b.sort_order || 0);
          }
          return (a.code || '').localeCompare(b.code || '');
        });
        setPhaseCategories(categories);
      }
    } catch (error) {
      console.error('获取项目阶段分类失败:', error);
    }
  };

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

    // 按阶段分类筛选
    if (selectedCategory !== 'all') {
      filteredPhases = filteredPhases.filter((phase) => phase.category_id === selectedCategory);
    }

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
      filteredPhases = filteredPhases.filter((phase) => {
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

    // 按阶段分类分组统计
    const phasesByCategory: Record<string, number> = {};
    filteredPhases.forEach((phase) => {
      const categoryName = phase.category_name || phaseCategories.find(c => c.id === phase.category_id)?.name || '未知阶段';
      phasesByCategory[categoryName] = (phasesByCategory[categoryName] || 0) + 1;
    });

    // 按阶段代码统计（01-准备/可研, 02-寻源, 03-实施, 04-交付, 05-收尾）
    const phasesByStage: Record<string, {
      count: number;
      completed: number;
      inProgress: number;
      notStarted: number;
      averageProgress: number;
    }> = {};

    // 定义阶段映射
    const stageMapping: Record<string, string> = {
      '01-': '01-准备/可研',
      '02-': '02-寻源',
      '03-': '03-实施',
      '04-': '04-交付',
      '05-': '05-收尾',
    };

    filteredPhases.forEach((phase) => {
      const category = phaseCategories.find(c => c.id === phase.category_id);
      if (category && category.code) {
        // 查找匹配的阶段代码前缀
        const stageKey = Object.keys(stageMapping).find(key => category.code.startsWith(key));
        if (stageKey) {
          const stageName = stageMapping[stageKey];
          if (!phasesByStage[stageName]) {
            phasesByStage[stageName] = {
              count: 0,
              completed: 0,
              inProgress: 0,
              notStarted: 0,
              averageProgress: 0,
            };
          }
          phasesByStage[stageName].count++;
          if (phase.progress_percent >= 100) {
            phasesByStage[stageName].completed++;
          } else if (phase.progress_percent > 0) {
            phasesByStage[stageName].inProgress++;
          } else {
            phasesByStage[stageName].notStarted++;
          }
        }
      }
    });

    // 计算每个阶段的平均进度
    Object.keys(phasesByStage).forEach((stageName) => {
      const stagePhases = filteredPhases.filter((phase) => {
        const category = phaseCategories.find(c => c.id === phase.category_id);
        if (category && category.code) {
          const stageKey = Object.keys(stageMapping).find(key => category.code.startsWith(key));
          return stageKey && stageMapping[stageKey] === stageName;
        }
        return false;
      });
      if (stagePhases.length > 0) {
        phasesByStage[stageName].averageProgress =
          stagePhases.reduce((sum, p) => sum + p.progress_percent, 0) / stagePhases.length;
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
      phasesByCategory,
      phasesByProject,
      phasesByStage,
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
      筛选阶段:
        selectedCategory === 'all'
          ? '所有阶段'
          : phaseCategories.find((c) => c.id === selectedCategory)?.name || selectedCategory,
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
      按阶段分类统计: statistics.phasesByCategory,
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
          <p className="text-gray-600 mt-1">项目阶段进度统计与分析（按基础数据阶段分类）</p>
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
            <label className="block text-sm font-medium text-gray-700 mb-2">阶段分类</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">所有阶段</option>
              {phaseCategories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name} ({category.code})
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

          {/* 按阶段统计（01-准备/可研, 02-寻源, 03-实施, 04-交付, 05-收尾） */}
          {Object.keys(statistics.phasesByStage).length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-md">
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">按阶段统计</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {['01-准备/可研', '02-寻源', '03-实施', '04-交付', '05-收尾'].map((stageName) => {
                  const stageData = statistics.phasesByStage[stageName];
                  if (!stageData || stageData.count === 0) return null;

                  const stageColors: Record<string, { bg: string; text: string; border: string; progress: string }> = {
                    '01-准备/可研': {
                      bg: 'from-blue-50 to-blue-100',
                      text: 'text-blue-700',
                      border: 'border-blue-200',
                      progress: 'from-blue-500 to-blue-600',
                    },
                    '02-寻源': {
                      bg: 'from-purple-50 to-purple-100',
                      text: 'text-purple-700',
                      border: 'border-purple-200',
                      progress: 'from-purple-500 to-purple-600',
                    },
                    '03-实施': {
                      bg: 'from-green-50 to-green-100',
                      text: 'text-green-700',
                      border: 'border-green-200',
                      progress: 'from-green-500 to-green-600',
                    },
                    '04-交付': {
                      bg: 'from-orange-50 to-orange-100',
                      text: 'text-orange-700',
                      border: 'border-orange-200',
                      progress: 'from-orange-500 to-orange-600',
                    },
                    '05-收尾': {
                      bg: 'from-red-50 to-red-100',
                      text: 'text-red-700',
                      border: 'border-red-200',
                      progress: 'from-red-500 to-red-600',
                    },
                  };

                  const colors = stageColors[stageName] || {
                    bg: 'from-gray-50 to-gray-100',
                    text: 'text-gray-700',
                    border: 'border-gray-200',
                    progress: 'from-gray-500 to-gray-600',
                  };

                  return (
                    <div
                      key={stageName}
                      className={`bg-gradient-to-br ${colors.bg} rounded-2xl shadow-lg border-2 ${colors.border} p-6 hover:shadow-xl hover:scale-[1.02] transition-all duration-200`}
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h4 className={`text-lg font-bold ${colors.text}`}>{stageName}</h4>
                        <div className={`px-3 py-1 bg-white/50 rounded-lg ${colors.text} font-semibold text-sm`}>
                          {stageData.count}
                        </div>
                      </div>

                      {/* 平均进度 */}
                      <div className="mb-4">
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className={`font-medium ${colors.text}`}>平均进度</span>
                          <span className={`font-bold text-xl ${colors.text}`}>
                            {stageData.averageProgress.toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-white/50 rounded-full h-3 overflow-hidden">
                          <div
                            className={`bg-gradient-to-r ${colors.progress} h-3 rounded-full transition-all duration-500 shadow-sm`}
                            style={{ width: `${stageData.averageProgress}%` }}
                          />
                        </div>
                      </div>

                      {/* 状态统计 */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4 text-green-600" />
                            已完成
                          </span>
                          <span className="font-semibold text-gray-900">{stageData.completed}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 flex items-center gap-1">
                            <Clock className="w-4 h-4 text-yellow-600" />
                            进行中
                          </span>
                          <span className="font-semibold text-gray-900">{stageData.inProgress}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 flex items-center gap-1">
                            <AlertCircle className="w-4 h-4 text-gray-400" />
                            未开始
                          </span>
                          <span className="font-semibold text-gray-900">{stageData.notStarted}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 按阶段分类统计 */}
          {Object.keys(statistics.phasesByCategory).length > 0 && (
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">按阶段分类统计</h3>
              <div className="space-y-3">
                {Object.entries(statistics.phasesByCategory)
                  .sort(([, a], [, b]) => b - a)
                  .map(([categoryName, count]) => (
                    <div key={categoryName}>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-700 truncate">{categoryName}</span>
                        <span className="font-medium text-gray-900">{count}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-500 h-2 rounded-full transition-all"
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
