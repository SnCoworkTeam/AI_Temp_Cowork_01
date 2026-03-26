'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  Settings,
  MessageSquare,
  Bot,
  GitBranch,
  BookOpen,
  Network,
  Building2,
  Component,
  Users,
  Wrench,
  FileText,
  Database,
  Activity,
  Server,
  Calendar,
  BarChart3,
  Zap,
  Shield,
  Globe,
  Sparkles,
  CheckSquare,
  Bell,
  Briefcase,
  Star,
  HelpCircle,
  Megaphone,
  TrendingUp,
  Search,
  ArrowRight,
  Crown,
  Award,
  Target,
  X,
  Code2,
  MessageCircle,
} from 'lucide-react';

interface PortalCard {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  color: string;
  category: string;
  badge?: string;
}

export default function PortalPage() {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  const portalCards: PortalCard[] = [
    // 个人工作（新增）
    {
      id: 'todos',
      title: '待办事项',
      description: '个人待办事项管理，任务跟踪和提醒，支持优先级和截止日期',
      icon: CheckSquare,
      href: '/todos',
      color: 'red',
      category: '个人工作',
      badge: '新功能',
    },
    {
      id: 'notifications',
      title: '通知中心',
      description: '系统通知、消息提醒、项目更新通知，支持分类和已读管理',
      icon: Bell,
      href: '/notifications',
      color: 'red',
      category: '个人工作',
      badge: '新功能',
    },
    {
      id: 'workspace',
      title: '个人工作台',
      description: '个人工作概览、我的任务、我的项目、最近访问记录',
      icon: Briefcase,
      href: '/workspace',
      color: 'red',
      category: '个人工作',
    },
    {
      id: 'favorites',
      title: '收藏夹',
      description: '收藏常用功能模块，快速访问个人常用功能',
      icon: Star,
      href: '/favorites',
      color: 'red',
      category: '个人工作',
    },

    // 业务管理 - 按照菜单顺序排列，第一个是仪表盘
    {
      id: 'project-dashboard',
      title: '项目仪表盘',
      description: '项目概览、统计分析和可视化展示',
      icon: LayoutDashboard,
      href: '/projects/dashboard',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'projects',
      title: '项目列表',
      description: '查看和管理所有项目，包括项目创建、编辑、删除和详情查看',
      icon: FolderKanban,
      href: '/projects',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'create-project',
      title: '创建项目',
      description: '创建新项目，设置项目基本信息、阶段和里程碑',
      icon: FileText,
      href: '/projects/create',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'hello-world',
      title: 'Hello World',
      description: '测试页面：输入 hello world 显示你好全世界',
      icon: MessageCircle,
      href: '/projects/hello-world',
      color: 'green',
      category: '业务管理',
    },
    {
      id: 'project-programs',
      title: '项目群管理',
      description: '项目群创建、管理和统计分析，查看项目群下的所有项目',
      icon: Building2,
      href: '/projects/programs',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'plan-templates',
      title: '计划模板',
      description: '项目计划模板管理，创建和编辑计划模板',
      icon: FileText,
      href: '/projects/plans/templates',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'schedule',
      title: '进度计划',
      description: '项目进度计划管理和甘特图展示',
      icon: Calendar,
      href: '/projects/schedule',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'project-import',
      title: '项目导入',
      description: '批量导入项目数据，支持Excel格式导入',
      icon: FileText,
      href: '/projects/import',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'project-phases',
      title: '项目阶段',
      description: '项目阶段管理，创建和管理项目各阶段',
      icon: Calendar,
      href: '/projects/phases',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'phase-statistics',
      title: '阶段统计',
      description: '项目阶段进度统计与分析，按基础数据阶段分类统计',
      icon: BarChart3,
      href: '/projects/phase-statistics',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'tasks',
      title: '任务管理',
      description: '项目任务分配、跟踪和完成情况管理',
      icon: Activity,
      href: '/projects/tasks',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'weekly-reports',
      title: '周报管理',
      description: '项目周报创建、查看和管理',
      icon: FileText,
      href: '/projects/weekly-reports',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'monthly-reports',
      title: '月报管理',
      description: '项目月报创建、查看和管理',
      icon: FileText,
      href: '/projects/monthly-reports',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'progress-reports',
      title: '周月进度报告',
      description: '查看和管理项目的周报、月报，跟踪项目进度',
      icon: BarChart3,
      href: '/projects/progress-reports',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'reports',
      title: '报告管理',
      description: '项目报告管理和查看',
      icon: FileText,
      href: '/projects/reports',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'risks',
      title: '风险管理',
      description: '项目风险识别、评估和应对措施管理',
      icon: Shield,
      href: '/projects/risks',
      color: 'blue',
      category: '业务管理',
    },
    {
      id: 'basic-data',
      title: '基础数据维护',
      description: '维护项目分类、行业领域等基础数据',
      icon: Database,
      href: '/projects/basic-data',
      color: 'blue',
      category: '业务管理',
    },

    // AI与智能
    {
      id: 'ai-assistant',
      title: 'AI助手',
      description: '智能对话助手，支持自然语言交互和任务执行',
      icon: MessageSquare,
      href: '/chat',
      color: 'purple',
      category: 'AI智能',
      badge: '热门',
    },
    {
      id: 'agents',
      title: '智能体',
      description: '智能体管理和配置，支持多智能体协作',
      icon: Bot,
      href: '/agents',
      color: 'purple',
      category: 'AI智能',
    },
    {
      id: 'knowledge-base',
      title: '知识库',
      description: '文档管理、语义搜索和知识图谱构建',
      icon: BookOpen,
      href: '/knowledge-bases',
      color: 'purple',
      category: 'AI智能',
    },
    {
      id: 'knowledge-graph',
      title: '知识图谱',
      description: '可视化知识图谱，探索实体关系和知识网络',
      icon: Network,
      href: '/knowledge-graph',
      color: 'purple',
      category: 'AI智能',
    },

    // 工作流与自动化
    {
      id: 'workflows',
      title: '工作流列表',
      description: '查看和管理所有工作流定义',
      icon: GitBranch,
      href: '/workflows',
      color: 'green',
      category: '工作流',
    },
    {
      id: 'workflow-designer',
      title: '工作流设计器',
      description: '可视化工作流设计，拖拽式流程编排',
      icon: Component,
      href: '/workflow-designer',
      color: 'green',
      category: '工作流',
    },

    // 企业架构
    {
      id: 'enterprise-architecture',
      title: '企业架构',
      description: '企业架构总览，包括组织、业务、应用、数据和技术架构',
      icon: Building2,
      href: '/enterprise-architecture',
      color: 'orange',
      category: '企业架构',
    },
    {
      id: 'organization',
      title: '组织架构',
      description: '组织架构管理和可视化',
      icon: Users,
      href: '/enterprise-architecture/organization',
      color: 'orange',
      category: '企业架构',
    },
    {
      id: 'business-architecture',
      title: '业务架构',
      description: '业务架构设计和业务能力管理',
      icon: Building2,
      href: '/enterprise-architecture/business',
      color: 'orange',
      category: '企业架构',
    },
    {
      id: 'application-architecture',
      title: '应用架构',
      description: '应用系统架构和应用服务管理',
      icon: Component,
      href: '/enterprise-architecture/application',
      color: 'orange',
      category: '企业架构',
    },
    {
      id: 'data-architecture',
      title: '数据架构',
      description: '数据架构设计和数据资产管理',
      icon: Database,
      href: '/enterprise-architecture/data',
      color: 'orange',
      category: '企业架构',
    },
    {
      id: 'technology-architecture',
      title: '技术架构',
      description: '技术架构和技术栈管理',
      icon: Server,
      href: '/enterprise-architecture/technology',
      color: 'orange',
      category: '企业架构',
    },

    // 系统管理
    {
      id: 'admin-dashboard',
      title: '管理仪表板',
      description: '系统概览、统计数据和快速操作',
      icon: LayoutDashboard,
      href: '/admin/dashboard',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'users',
      title: '用户管理',
      description: '用户账户、角色和权限管理',
      icon: Users,
      href: '/admin/users',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'tools',
      title: '工具管理',
      description: 'MCP工具配置和管理',
      icon: Wrench,
      href: '/admin/tools',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'prompts',
      title: '提示词管理',
      description: 'AI提示词模板管理和优化',
      icon: FileText,
      href: '/admin/prompts',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'metadata',
      title: '元数据管理',
      description: '企业元数据资产管理和维护',
      icon: Database,
      href: '/admin/metadata',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'monitoring',
      title: '系统监控',
      description: '服务监控、日志查看和性能分析',
      icon: Activity,
      href: '/admin/monitoring',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'database',
      title: '数据库管理',
      description: '数据库概览、表管理和性能监控',
      icon: Database,
      href: '/admin/database/overview',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'opencode',
      title: 'OpenCode 开发',
      description: 'OpenCode 使用独立地址，与 19 服务不同；登录认证通过后跳转到 OpenCode',
      icon: Code2,
      href: '/opencode',
      color: 'gray',
      category: '系统管理',
    },
    {
      id: 'codex-cli',
      title: 'Codex CLI',
      description: '在门户内调用服务器已安装的 Codex CLI，配合内网大模型执行编码与自动化任务',
      icon: Code2,
      href: '/codex-cli',
      color: 'purple',
      category: 'AI智能',
      badge: '内网',
    },

    // 其他功能
    {
      id: 'conversations',
      title: '对话历史',
      description: '查看历史对话记录和会话管理',
      icon: MessageSquare,
      href: '/conversations',
      color: 'indigo',
      category: '其他',
    },
    {
      id: 'components',
      title: '组件库',
      description: '可复用组件库和UI组件',
      icon: Component,
      href: '/components',
      color: 'indigo',
      category: '其他',
    },
    {
      id: 'help',
      title: '帮助中心',
      description: '使用帮助文档、常见问题、操作指南和视频教程',
      icon: HelpCircle,
      href: '/help',
      color: 'indigo',
      category: '其他',
    },
    {
      id: 'announcements',
      title: '系统公告',
      description: '系统公告、重要通知和更新信息',
      icon: Megaphone,
      href: '/announcements',
      color: 'indigo',
      category: '其他',
    },
    {
      id: 'analytics',
      title: '数据看板',
      description: '个人数据统计、工作完成情况、效率分析和趋势图表',
      icon: TrendingUp,
      href: '/analytics',
      color: 'indigo',
      category: '其他',
    },
  ];

  const categories = Array.from(new Set(portalCards.map((card) => card.category)));

  const filteredCards = portalCards.filter((card) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      card.title.toLowerCase().includes(query) ||
      card.description.toLowerCase().includes(query) ||
      card.category.toLowerCase().includes(query)
    );
  });

  const groupedCards = categories.reduce(
    (acc, category) => {
      acc[category] = filteredCards.filter((card) => card.category === category);
      return acc;
    },
    {} as Record<string, PortalCard[]>
  );

  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500 hover:bg-blue-600 text-white',
    purple: 'bg-purple-500 hover:bg-purple-600 text-white',
    green: 'bg-green-500 hover:bg-green-600 text-white',
    orange: 'bg-orange-500 hover:bg-orange-600 text-white',
    gray: 'bg-gray-500 hover:bg-gray-600 text-white',
    indigo: 'bg-indigo-500 hover:bg-indigo-600 text-white',
    red: 'bg-red-500 hover:bg-red-600 text-white',
  };

  const iconBgClasses: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
    gray: 'bg-gray-100 text-gray-600',
    indigo: 'bg-indigo-100 text-indigo-600',
    red: 'bg-red-100 text-red-600',
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50">
      {/* 顶部横幅区域 */}
      <div className="relative bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 text-white overflow-hidden">
        {/* 装饰性背景元素 */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-blue-400 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-400 rounded-full blur-3xl"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20">
                  <Crown className="w-8 h-8 text-yellow-300" />
                </div>
                <div>
                  <h1 className="text-4xl md:text-5xl font-bold mb-2 bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                    中化国际AIOS平台
                  </h1>
                  <p className="text-blue-200 text-lg font-medium">
                    Sinochem International AIOS Platform
                  </p>
                </div>
              </div>
              <p className="text-blue-100 text-lg max-w-2xl leading-relaxed">
                欢迎回来，
                <span className="font-semibold text-white">{user?.username || '用户'}</span>
                。这里是您的智能工作门户，整合了项目管理、AI助手、企业架构等核心功能。
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-blue-200 mb-1">当前时间</div>
                <div className="text-2xl font-bold">
                  {new Date().toLocaleDateString('zh-CN', {
                    month: 'long',
                    day: 'numeric',
                    weekday: 'long',
                  })}
                </div>
              </div>
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center border-4 border-white/20 shadow-lg">
                <Users className="w-8 h-8 text-white" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10">
        {/* 搜索栏 - 提升设计 */}
        <div className="mb-12">
          <div className="relative bg-white rounded-2xl shadow-xl border border-gray-200 p-2">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl">
                <Search className="w-6 h-6 text-white" />
              </div>
              <input
                type="text"
                placeholder="搜索功能模块、服务或工具..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-4 py-4 text-lg border-0 focus:ring-0 focus:outline-none bg-transparent placeholder-gray-400"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
          {searchQuery && (
            <div className="mt-3 text-sm text-gray-600">
              找到 <span className="font-semibold text-blue-600">{filteredCards.length}</span>{' '}
              个匹配的功能模块
            </div>
          )}
        </div>

        {/* 功能卡片 */}
        {Object.entries(groupedCards).map(([category, cards]) => (
          <div key={category} className="mb-16">
            {/* 分类标题 - 更庄重的设计 */}
            <div className="mb-8 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-2 h-12 bg-gradient-to-b from-blue-600 via-indigo-600 to-purple-600 rounded-full shadow-lg"></div>
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-1">{category}</h2>
                  <div className="h-1 w-24 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full"></div>
                </div>
              </div>
              <div className="text-sm text-gray-500 font-medium">{cards.length} 个功能模块</div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {cards.map((card) => {
                const Icon = card.icon;
                return (
                  <a
                    key={card.id}
                    href={card.href}
                    className="group relative bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-200 hover:border-blue-400 hover:-translate-y-1"
                  >
                    {/* 卡片头部 - 更大气 */}
                    <div className={`relative ${colorClasses[card.color]} p-6 overflow-hidden`}>
                      {/* 背景装饰 */}
                      <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
                      <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full -ml-12 -mb-12"></div>

                      <div className="relative flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div
                            className={`p-3 rounded-xl ${iconBgClasses[card.color]} shadow-lg group-hover:scale-110 transition-transform duration-300`}
                          >
                            <Icon className="w-7 h-7" />
                          </div>
                          <h3 className="font-bold text-xl text-white">{card.title}</h3>
                        </div>
                        {card.badge && (
                          <span className="px-3 py-1.5 text-xs font-bold bg-white/25 backdrop-blur-sm rounded-full border border-white/30 shadow-sm">
                            {card.badge}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* 卡片内容 - 更优雅 */}
                    <div className="p-6">
                      <p className="text-gray-600 text-sm leading-relaxed mb-4 min-h-[3rem]">
                        {card.description}
                      </p>

                      {/* 底部操作区 */}
                      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                        <span className="text-sm font-semibold text-gray-700 group-hover:text-blue-600 transition-colors">
                          立即使用
                        </span>
                        <div className="p-2 bg-gray-50 rounded-lg group-hover:bg-blue-50 transition-colors">
                          <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                        </div>
                      </div>
                    </div>

                    {/* 悬停光效 */}
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 via-indigo-500/0 to-purple-500/0 group-hover:from-blue-500/5 group-hover:via-indigo-500/5 group-hover:to-purple-500/5 transition-all duration-300 pointer-events-none"></div>
                  </a>
                );
              })}
            </div>
          </div>
        ))}

        {/* 无搜索结果提示 */}
        {filteredCards.length === 0 && searchQuery && (
          <div className="text-center py-20 bg-white rounded-2xl shadow-lg border border-gray-200">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-6">
              <Search className="w-10 h-10 text-gray-400" />
            </div>
            <p className="text-gray-700 text-xl font-semibold mb-2">未找到匹配的功能模块</p>
            <p className="text-gray-500 text-sm">请尝试其他搜索关键词或浏览所有功能分类</p>
          </div>
        )}

        {/* 统计信息 - 更庄重的设计 */}
        <div className="mt-16 mb-12 relative">
          {/* 背景装饰 */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-3xl opacity-5 blur-3xl"></div>

          <div className="relative bg-white rounded-3xl shadow-2xl border border-gray-200 overflow-hidden">
            {/* 顶部装饰条 */}
            <div className="h-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600"></div>

            <div className="p-8">
              <div className="flex items-center gap-3 mb-6">
                <Award className="w-6 h-6 text-blue-600" />
                <h3 className="text-xl font-bold text-gray-900">平台概览</h3>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                <div className="text-center group">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-100 to-blue-200 mb-4 group-hover:scale-110 transition-transform shadow-lg">
                    <Target className="w-8 h-8 text-blue-600" />
                  </div>
                  <p className="text-4xl font-bold text-blue-600 mb-2">{portalCards.length}</p>
                  <p className="text-gray-600 font-medium">功能模块</p>
                  <p className="text-gray-400 text-xs mt-1">全面覆盖业务需求</p>
                </div>

                <div className="text-center group">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-100 to-purple-200 mb-4 group-hover:scale-110 transition-transform shadow-lg">
                    <LayoutDashboard className="w-8 h-8 text-purple-600" />
                  </div>
                  <p className="text-4xl font-bold text-purple-600 mb-2">{categories.length}</p>
                  <p className="text-gray-600 font-medium">功能分类</p>
                  <p className="text-gray-400 text-xs mt-1">系统化管理</p>
                </div>

                <div className="text-center group">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-green-100 to-green-200 mb-4 group-hover:scale-110 transition-transform shadow-lg">
                    <Activity className="w-8 h-8 text-green-600" />
                  </div>
                  <p className="text-4xl font-bold text-green-600 mb-2">24/7</p>
                  <p className="text-gray-600 font-medium">服务可用</p>
                  <p className="text-gray-400 text-xs mt-1">持续稳定运行</p>
                </div>

                <div className="text-center group">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-100 to-orange-200 mb-4 group-hover:scale-110 transition-transform shadow-lg">
                    <Shield className="w-8 h-8 text-orange-600" />
                  </div>
                  <p className="text-4xl font-bold text-orange-600 mb-2">100%</p>
                  <p className="text-gray-600 font-medium">数据安全</p>
                  <p className="text-gray-400 text-xs mt-1">企业级保障</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
