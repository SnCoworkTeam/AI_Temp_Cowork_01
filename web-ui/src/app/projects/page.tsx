'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Plus, Upload, Search, Calendar, TrendingUp, FileText, Layers } from 'lucide-react';
import { apiGatewayClient } from '@/lib/api/client';
import Link from 'next/link';
import ProjectPhaseProgress from '@/components/ProjectPhaseProgress';

interface BasicDataCategory {
  id: string;
  category_type: string;
  code: string;
  name: string;
}

interface Project {
  id: string;
  project_code: string;
  name: string;
  status: string;
  progress_percent: number;
  created_at: string;
  requires_weekly_report?: boolean;
  basic_data_categories?: BasicDataCategory[];
}

interface PhaseCategory {
  id: string;
  code: string;
  name: string;
  sort_order: number;
}

export default function AdminProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all'); // 页签选择
  const [phases, setPhases] = useState<PhaseCategory[]>([]); // 项目阶段列表（统一获取）

  useEffect(() => {
    fetchProjects();
    fetchPhases(); // 统一获取阶段列表
  }, []);

  // 统一获取项目阶段列表（只获取一次）
  const fetchPhases = async () => {
    try {
      // 使用合理的limit值，避免422错误
      try {
        const data = await apiGatewayClient.get<{ items: PhaseCategory[] }>(
          '/api/v1/basic-data/categories?category_type=project_phase&limit=100'
        );
        const phaseList = (data.items || []).filter((cat: any) => cat.is_active !== false);

        // 按sort_order排序，如果没有sort_order则按code排序
        phaseList.sort((a: PhaseCategory, b: PhaseCategory) => {
          if (a.sort_order !== b.sort_order) {
            return (a.sort_order || 0) - (b.sort_order || 0);
          }
          return (a.code || '').localeCompare(b.code || '');
        });
        setPhases(phaseList);
      } catch (error: any) {
        if (error?.statusCode === 422) {
          console.warn('获取项目阶段列表遇到422错误，尝试不使用limit参数');
          const data = await apiGatewayClient.get<{ items: PhaseCategory[] }>(
            '/api/v1/basic-data/categories?category_type=project_phase'
          );
          const phaseList = (data.items || []).filter((cat: any) => cat.is_active !== false);
          phaseList.sort((a: PhaseCategory, b: PhaseCategory) => {
            if (a.sort_order !== b.sort_order) {
              return (a.sort_order || 0) - (b.sort_order || 0);
            }
            return (a.code || '').localeCompare(b.code || '');
          });
          setPhases(phaseList);
        } else {
          throw error;
        }
      }
    } catch (error) {
      console.error('加载项目阶段列表失败:', error);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await apiGatewayClient.get<{ items: Project[] }>('/api/v1/projects');
      setProjects(data.items || []);
    } catch (error) {
      console.error('获取项目列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-gray-500',
      active: 'bg-blue-500',
      delayed: 'bg-yellow-500',
      completed: 'bg-green-500',
      cancelled: 'bg-red-500',
    };
    return colors[status] || 'bg-gray-500';
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

  // 分类列表
  const categories = [
    { value: 'all', label: '全部' },
    { value: '基设网安', label: '基设网安' },
    { value: '业务经营', label: '业务经营' },
    { value: '管理应用', label: '管理应用' },
    { value: '生产运营', label: '生产运营' },
    { value: '瑞恒基地', label: '瑞恒基地' },
  ];

  // 获取项目的分类（基于project_category）
  const getProjectCategory = (project: Project): string | null => {
    if (!project.basic_data_categories || project.basic_data_categories.length === 0) {
      return null;
    }
    const categoryCategory = project.basic_data_categories.find(
      (cat) => cat.category_type === 'project_category'
    );
    return categoryCategory ? categoryCategory.name : null;
  };

  // 获取项目的阶段（基于project_phase）
  const getProjectPhase = (project: Project): string | null => {
    if (!project.basic_data_categories || project.basic_data_categories.length === 0) {
      return null;
    }
    const phaseCategory = project.basic_data_categories.find(
      (cat) => cat.category_type === 'project_phase'
    );
    if (!phaseCategory) return null;

    // 去掉阶段名称中的前缀（如"01-"、"02-"等），只返回纯名称
    let phaseName = phaseCategory.name || '';
    phaseName = phaseName.replace(/^\d{2}-/, '');
    return phaseName;
  };

  // 过滤项目（按分类和搜索）
  const filteredProjects = useMemo(() => {
    let filtered = projects.filter(
      (project) =>
        project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.project_code.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // 按分类过滤
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((project) => {
        const projectCategory = getProjectCategory(project);
        return projectCategory === selectedCategory;
      });
    }

    return filtered;
  }, [projects, searchTerm, selectedCategory]);

  // 按项目阶段分组
  const projectsByPhase = useMemo(() => {
    const grouped: Record<string, Project[]> = {};
    const otherPhase = '其他阶段';

    // 定义项目阶段的显示顺序
    const phaseOrder: Record<string, number> = {
      '准备/可研': 1,
      寻源: 2,
      实施: 3,
      交付: 4,
      收尾: 5,
    };

    filteredProjects.forEach((project) => {
      const phase = getProjectPhase(project) || otherPhase;
      if (!grouped[phase]) {
        grouped[phase] = [];
      }
      grouped[phase].push(project);
    });

    // 按阶段排序（按照指定的顺序）
    const sortedPhases = Object.keys(grouped).sort((a, b) => {
      // 将"其他阶段"放在最后
      if (a === otherPhase) return 1;
      if (b === otherPhase) return -1;

      // 按照预定义的顺序排序
      const orderA = phaseOrder[a] || 999;
      const orderB = phaseOrder[b] || 999;

      if (orderA !== orderB) {
        return orderA - orderB;
      }

      // 如果不在预定义列表中，按字母顺序排序
      return a.localeCompare(b, 'zh-CN');
    });

    return { grouped, sortedPhases };
  }, [filteredProjects]);

  return (
    <div className="space-y-6">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            项目列表
          </h1>
          <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            管理和查看所有项目信息
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/projects/import"
            className="px-5 py-2.5 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 flex items-center gap-2 font-medium shadow-sm hover:shadow-md"
          >
            <Upload className="h-4 w-4" />
            导入Excel
          </Link>
          <Link
            href="/projects/create"
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            新建项目
          </Link>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-sm border border-blue-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-700 mb-1">总项目数</p>
              <p className="text-2xl font-bold text-blue-900">{projects.length}</p>
            </div>
            <div className="p-3 bg-blue-200 rounded-lg">
              <FileText className="h-6 w-6 text-blue-700" />
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl shadow-sm border border-green-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-700 mb-1">进行中</p>
              <p className="text-2xl font-bold text-green-900">
                {projects.filter((p) => p.status === 'active').length}
              </p>
            </div>
            <div className="p-3 bg-green-200 rounded-lg">
              <TrendingUp className="h-6 w-6 text-green-700" />
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl shadow-sm border border-yellow-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-700 mb-1">已延迟</p>
              <p className="text-2xl font-bold text-yellow-900">
                {projects.filter((p) => p.status === 'delayed').length}
              </p>
            </div>
            <div className="p-3 bg-yellow-200 rounded-lg">
              <Calendar className="h-6 w-6 text-yellow-700" />
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl shadow-sm border border-emerald-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-emerald-700 mb-1">需周报</p>
              <p className="text-2xl font-bold text-emerald-900">
                {projects.filter((p) => p.requires_weekly_report).length}
              </p>
            </div>
            <div className="p-3 bg-emerald-200 rounded-lg">
              <FileText className="h-6 w-6 text-emerald-700" />
            </div>
          </div>
        </div>
      </div>

      {/* 页签 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-4">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category.value}
              onClick={() => setSelectedCategory(category.value)}
              className={`px-5 py-2.5 rounded-xl font-medium transition-all duration-200 flex items-center gap-2 ${
                selectedCategory === category.value
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
              }`}
            >
              <Layers className="h-4 w-4" />
              {category.label}
              {selectedCategory === category.value && (
                <span className="ml-1 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {filteredProjects.length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-5">
        <div className="relative">
          <Search className="absolute left-5 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="搜索项目名称或编码..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-14 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm bg-gray-50 focus:bg-white"
          />
        </div>
      </div>

      {/* 项目列表 */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
            <Search className="h-8 w-8 text-gray-400" />
          </div>
          <p className="text-gray-600 font-medium mb-2">暂无项目</p>
          <p className="text-sm text-gray-500 mb-6">开始创建您的第一个项目</p>
          <Link
            href="/projects/import"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
          >
            <Upload className="h-4 w-4" />
            导入Excel项目
          </Link>
        </div>
      ) : (
        <div className="space-y-8">
          {/* 按项目阶段分组展示 */}
          {projectsByPhase.sortedPhases.length > 0 ? (
            projectsByPhase.sortedPhases.map((phase) => {
              const phaseProjects = projectsByPhase.grouped[phase] || [];
              if (phaseProjects.length === 0) return null;

              return (
                <div key={phase} className="space-y-4">
                  {/* 阶段标题 - 美化（缩小版） */}
                  <div className="relative bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-xl p-3 border-2 border-blue-200 shadow-md">
                    <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-xl"></div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-md transform rotate-3 hover:rotate-6 transition-transform">
                          <Layers className="h-4 w-4 text-white" />
                        </div>
                        <div>
                          <h2 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                            {phase}
                          </h2>
                          <p className="text-xs text-gray-600 mt-0.5">项目阶段分类</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="px-3 py-1.5 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm border-2 border-blue-200">
                          <span className="text-lg font-bold text-blue-600">
                            {phaseProjects.length}
                          </span>
                          <span className="text-xs text-gray-600 ml-1.5">个项目</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 该阶段的项目列表 - 4列布局 */}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {phaseProjects.map((project) => {
                      // 验证项目ID是否为有效的UUID
                      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
                      const isValidProjectId = project.id && uuidRegex.test(project.id);

                      if (!isValidProjectId) {
                        console.warn('无效的项目ID，跳过:', project.id);
                        return null;
                      }

                      return (
                      <Link key={project.id} href={`/projects/${project.id}`}>
                        <div className="group relative bg-white rounded-xl shadow-md border-2 border-gray-200 hover:shadow-xl hover:border-blue-400 transition-all duration-300 cursor-pointer overflow-hidden transform hover:scale-[1.02] hover:-translate-y-0.5">
                          {/* 顶部渐变装饰条 */}
                          <div
                            className={`h-1.5 bg-gradient-to-r ${getStatusColor(project.status)} opacity-90 group-hover:opacity-100 transition-opacity`}
                          ></div>

                          {/* 背景装饰图案 */}
                          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-full -mr-12 -mt-12 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

                          <div className="relative p-4">
                            {/* 项目标题和状态 */}
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex-1 min-w-0 pr-2">
                                <div className="flex items-center gap-1.5 mb-1.5">
                                  <div className="p-1 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-md group-hover:from-blue-200 group-hover:to-indigo-200 transition-colors">
                                    <FileText className="h-3 w-3 text-blue-600" />
                                  </div>
                                  <h3 className="text-base font-bold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                                    {project.name}
                                  </h3>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <p className="text-xs text-gray-500 font-mono bg-gradient-to-r from-gray-50 to-gray-100 px-2 py-1 rounded-md border border-gray-200 shadow-sm">
                                    {project.project_code}
                                  </p>
                                </div>
                              </div>
                              <span
                                className={`px-2 py-1 text-xs font-bold rounded-lg ${getStatusColor(project.status)} text-white shadow-md flex-shrink-0 ml-1.5 transform group-hover:scale-105 transition-transform`}
                              >
                                {getStatusText(project.status)}
                              </span>
                            </div>

                            {/* 项目阶段进度 - 美化（缩小版） */}
                            <div className="mb-3 p-3 bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 rounded-lg border border-blue-100 shadow-inner group-hover:border-blue-200 group-hover:shadow-sm transition-all">
                              <div className="flex items-center justify-between text-xs mb-2">
                                <span className="text-gray-700 font-semibold flex items-center gap-1.5">
                                  <div className="p-1 bg-blue-100 rounded-md">
                                    <TrendingUp className="h-3 w-3 text-blue-600" />
                                  </div>
                                  <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent text-xs">
                                    项目阶段
                                  </span>
                                </span>
                              </div>
                              <div className="bg-white/60 backdrop-blur-sm rounded-md p-2 border border-blue-100">
                                <ProjectPhaseProgress
                                  currentPhase={(() => {
                                    // 从项目分类中获取项目阶段（来源于基础数据）
                                    if (
                                      project.basic_data_categories &&
                                      project.basic_data_categories.length > 0
                                    ) {
                                      const phaseCategory = project.basic_data_categories.find(
                                        (cat) => cat.category_type === 'project_phase'
                                      );
                                      if (phaseCategory) {
                                        // 优先使用ID（最准确），确保数据来源于基础数据
                                        return phaseCategory.id;
                                      }
                                    }
                                    return undefined;
                                  })()}
                                  phases={phases} // 传入统一的阶段列表，避免重复请求
                                  className="py-1"
                                />
                              </div>
                            </div>

                            {/* 底部信息 - 美化（缩小版） */}
                            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                              <div className="flex items-center gap-1.5 text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded-md border border-gray-200">
                                <Calendar className="h-3 w-3 text-blue-500" />
                                <span className="font-medium text-xs">
                                  {new Date(project.created_at).toLocaleDateString('zh-CN')}
                                </span>
                              </div>
                              <div className="flex items-center gap-1.5">
                                {project.requires_weekly_report && (
                                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold bg-gradient-to-r from-emerald-400 to-emerald-500 text-white shadow-md transform group-hover:scale-105 transition-transform">
                                    <FileText className="h-3 w-3" />
                                    需周报
                                  </span>
                                )}
                                <div className="w-1.5 h-1.5 rounded-full bg-blue-400 group-hover:bg-blue-500 transition-colors"></div>
                              </div>
                            </div>
                          </div>

                          {/* 悬停时的光效 */}
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-50/0 to-transparent opacity-0 group-hover:opacity-100 group-hover:via-blue-50/30 transition-opacity duration-500 pointer-events-none"></div>
                        </div>
                      </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                <Search className="h-8 w-8 text-gray-400" />
              </div>
              <p className="text-gray-600 font-medium mb-2">暂无项目</p>
              <p className="text-sm text-gray-500 mb-6">当前筛选条件下没有找到项目</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

