'use client';

import Link from 'next/link';
import { memo, useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard,
  Settings,
  Users,
  GitBranch,
  Wrench,
  Database,
  Activity,
  MessageSquare,
  Bot,
  BookOpen,
  FileText,
  Network,
  Building2,
  Component,
  FolderKanban,
  Calendar,
  Server,
  BarChart3,
  HardDrive,
  LucideIcon,
  ChevronDown,
  ChevronRight,
  Shield,
  Key,
  Menu,
  CheckSquare,
  Bell,
  Briefcase,
  Star,
  HelpCircle,
  Megaphone,
  TrendingUp,
  Code2,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon | string;
  children?: NavItem[];
  requiredPermission?: string; // 需要的权限代码（如 "admin:manage"）
  requireAdmin?: boolean; // 是否需要管理员权限
}

export const Sidebar = memo(function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuth();
  const pathname = usePathname();
  // 默认所有菜单都折叠，只有用户手动展开或路径匹配时才展开
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [collapsedItems, setCollapsedItems] = useState<Set<string>>(new Set());
  const [userPermissions, setUserPermissions] = useState<string[]>([]);

  // 获取用户权限
  useEffect(() => {
    const fetchUserPermissions = async () => {
      if (!user) {
        setUserPermissions([]);
        return;
      }

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        if (!token) return;

        // 从用户信息中获取权限（如果已有）
        if (user.permissions && Array.isArray(user.permissions)) {
          setUserPermissions(user.permissions);
          return;
        }

        // 如果没有，从API获取
        const response = await fetch(`${apiUrl}/api/users/me/permissions`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          setUserPermissions(data.permissions || []);
        }
      } catch (error) {
        console.error('获取用户权限失败:', error);
        // 如果API失败，尝试从用户信息中获取
        if (user.permissions && Array.isArray(user.permissions)) {
          setUserPermissions(user.permissions);
        }
      }
    };

    fetchUserPermissions();
  }, [user]);

  // 检查用户是否有权限
  const hasPermission = (permissionCode?: string, requireAdmin?: boolean): boolean => {
    if (!user) return false;

    // 检查是否需要管理员权限
    if (requireAdmin) {
      const isAdmin =
        user.username?.toLowerCase() === 'admin' ||
        user.roles?.some((r: string) => r.toLowerCase() === 'admin');
      if (!isAdmin) return false;
    }

    // 如果没有指定权限要求，默认允许
    if (!permissionCode) return true;

    // 检查用户是否有该权限
    return userPermissions.includes(permissionCode);
  };

  // 过滤菜单项（递归）
  const filterMenuByPermissions = (items: NavItem[]): NavItem[] => {
    return items
      .filter((item) => {
        // 检查当前菜单项的权限
        if (!hasPermission(item.requiredPermission, item.requireAdmin)) {
          return false;
        }
        return true;
      })
      .map((item) => {
        // 如果有子菜单，递归过滤
        if (item.children && item.children.length > 0) {
          const filteredChildren = filterMenuByPermissions(item.children);
          // 如果过滤后没有子菜单，且当前菜单项是父级菜单（href为#），则隐藏
          if (filteredChildren.length === 0 && item.href === '#') {
            return null;
          }
          return {
            ...item,
            children: filteredChildren.length > 0 ? filteredChildren : undefined,
          };
        }
        return item;
      })
      .filter((item): item is NavItem => item !== null);
  };

  const adminNavigation: NavItem[] = [
    { name: '仪表板', href: '/dashboard', icon: LayoutDashboard },

    // 个人工作
    {
      name: '个人工作',
      href: '#',
      icon: Briefcase,
      children: [
        { name: '待办事项', href: '/todos', icon: CheckSquare },
        { name: '通知中心', href: '/notifications', icon: Bell },
        { name: '个人工作台', href: '/workspace', icon: Briefcase },
        { name: '收藏夹', href: '/favorites', icon: Star },
      ],
    },

    // 业务管理
    {
      name: '业务管理',
      href: '#',
      icon: FolderKanban,
      children: [
        {
          name: '项目管理',
          href: '/projects',
          icon: FolderKanban,
          children: [
            { name: '仪表盘', href: '/projects/dashboard', icon: LayoutDashboard },
            { name: '项目列表', href: '/projects', icon: FolderKanban },
            { name: '创建项目', href: '/projects/create', icon: FileText },
            { name: 'Hello World', href: '/projects/hello-world', icon: FileText },
            { name: '项目群管理', href: '/projects/programs', icon: Building2 },
            { name: '计划模板', href: '/projects/plans/templates', icon: FileText },
            { name: '进度计划', href: '/projects/schedule', icon: Calendar },
            { name: '项目导入', href: '/projects/import', icon: FileText },
            { name: '阶段统计', href: '/projects/phase-statistics', icon: BarChart3 },
            { name: '任务管理', href: '/projects/tasks', icon: Activity },
            { name: '周报管理', href: '/projects/weekly-reports', icon: FileText },
            { name: '月报管理', href: '/projects/monthly-reports', icon: FileText },
            { name: '周月进度报告', href: '/projects/progress-reports', icon: BarChart3 },
            { name: '报告管理', href: '/projects/reports', icon: FileText },
            { name: '风险管理', href: '/projects/risks', icon: Activity },
            { name: '基础数据维护', href: '/projects/basic-data', icon: Database },
          ],
        },
        {
          name: '运营管理',
          href: '#',
          icon: TrendingUp,
          children: [
            {
              name: '行业报告自动化',
              href: '/business/industry-report',
              icon: FileText,
            },
          ],
        },
      ],
    },

    // AI智能
    {
      name: 'AI智能',
      href: '#',
      icon: Bot,
      children: [
        { name: 'AI助手', href: '/chat', icon: MessageSquare },
        { name: '智能体', href: '/agents', icon: Bot },
        { name: '场景库', href: '/ai-scenarios', icon: FolderKanban },
        { name: '知识库', href: '/knowledge-bases', icon: BookOpen },
        { name: '知识图谱', href: '/knowledge-graph', icon: Network },
        { name: '对话历史', href: '/conversations', icon: MessageSquare },
      ],
    },

    // 工作流
    {
      name: '工作流',
      href: '#',
      icon: GitBranch,
      children: [
        { name: '工作流列表', href: '/workflows', icon: GitBranch },
        { name: '工作流设计器', href: '/workflow-designer', icon: Component },
      ],
    },

    // 企业架构
    {
      name: '企业架构',
      href: '#',
      icon: Building2,
      children: [
        { name: '总览', href: '/enterprise-architecture', icon: LayoutDashboard },
        { name: '组织架构', href: '/enterprise-architecture/organization', icon: Users },
        { name: '业务架构', href: '/enterprise-architecture/business', icon: Building2 },
        { name: '应用架构', href: '/enterprise-architecture/application', icon: Component },
        { name: '数据架构', href: '/enterprise-architecture/data', icon: Database },
        { name: '技术架构', href: '/enterprise-architecture/technology', icon: Wrench },
        { name: '技术实例', href: '/enterprise-architecture/technology/instances', icon: Server },
        {
          name: '技术标准化',
          href: '/enterprise-architecture/technology/standardization',
          icon: BarChart3,
        },
        { name: '架构关系图', href: '/enterprise-architecture/relationships', icon: Network },
      ],
    },

    // 系统管理
    {
      name: '系统管理',
      href: '#',
      icon: Settings,
      requireAdmin: true, // 系统管理需要管理员权限
      children: [
        {
          name: '权限管理',
          href: '/admin/permissions',
          icon: Shield,
          requireAdmin: true,
          children: [
            { name: '用户管理', href: '/admin/permissions/users', icon: Users, requireAdmin: true },
            {
              name: '角色管理',
              href: '/admin/permissions/roles',
              icon: Shield,
              requireAdmin: true,
            },
            {
              name: '权限管理',
              href: '/admin/permissions/permissions',
              icon: Key,
              requireAdmin: true,
            },
            { name: '菜单权限', href: '/admin/permissions/menus', icon: Menu, requireAdmin: true },
          ],
        },
        { name: '工作流管理', href: '/admin/workflows', icon: GitBranch, requireAdmin: true },
        { name: '工具管理', href: '/admin/tools', icon: Wrench, requireAdmin: true },
        {
          name: '提示词管理',
          href: '/admin/prompts',
          icon: FileText,
          requireAdmin: true,
          children: [
            { name: '提示词列表', href: '/admin/prompts', icon: FileText, requireAdmin: true },
            {
              name: '创建提示词',
              href: '/admin/prompts/create',
              icon: FileText,
              requireAdmin: true,
            },
          ],
        },
        { name: '元数据管理', href: '/admin/metadata', icon: Database, requireAdmin: true },
        {
          name: 'OpenCode 开发',
          href: '/opencode',
          icon: Code2,
          requireAdmin: true,
        },
        {
          name: '系统监控',
          href: '/admin/monitoring',
          icon: Activity,
          requireAdmin: true,
          children: [
            { name: '监控总览', href: '/admin/monitoring', icon: BarChart3, requireAdmin: true },
            {
              name: '服务监控',
              href: '/admin/monitoring/services',
              icon: Server,
              requireAdmin: true,
            },
            {
              name: '日志查看',
              href: '/admin/monitoring/logs',
              icon: FileText,
              requireAdmin: true,
            },
            {
              name: '自动调试',
              href: '/admin/auto-debug/decision-panel',
              icon: Wrench,
              requireAdmin: true,
            },
          ],
        },
        {
          name: '数据库管理',
          href: '/admin/database/overview',
          icon: Database,
          requireAdmin: true,
          children: [
            {
              name: '数据库概览',
              href: '/admin/database/overview',
              icon: Database,
              requireAdmin: true,
            },
            { name: '表管理', href: '/admin/database/tables', icon: HardDrive, requireAdmin: true },
            {
              name: '性能监控',
              href: '/admin/database/performance',
              icon: BarChart3,
              requireAdmin: true,
            },
            {
              name: '备份管理',
              href: '/admin/database/backups',
              icon: HardDrive,
              requireAdmin: true,
            },
            { name: '图数据库', href: '/admin/database/neo4j', icon: Network, requireAdmin: true },
            { name: 'Neo4j图谱', href: '/neo4j-graph', icon: Network, requireAdmin: true },
          ],
        },
      ],
    },

    // 其他
    {
      name: '其他',
      href: '#',
      icon: Component,
      children: [
        { name: '组件库', href: '/components', icon: Component },
        { name: '帮助中心', href: '/help', icon: HelpCircle },
        { name: '系统公告', href: '/announcements', icon: Megaphone },
        { name: '数据看板', href: '/data-dashboard', icon: TrendingUp },
      ],
    },
  ];

  const isActive = (href: string, item: NavItem) => {
    if (!pathname) return false;

    // 精确匹配
    if (href === pathname) {
      // 如果是父菜单（有子菜单），只有当没有子菜单匹配时才选中
      if (item.children && item.children.length > 0) {
        // 检查是否有子菜单匹配当前路径
        const hasMatchingChild = item.children.some((child) => {
          if (pathname === child.href) return true;
          if (child.href && pathname.startsWith(child.href + '/')) return true;
          // 递归检查更深层的子菜单
          if (child.children) {
            return child.children.some((grandChild) => {
              if (pathname === grandChild.href) return true;
              if (grandChild.href && pathname.startsWith(grandChild.href + '/')) return true;
              return false;
            });
          }
          return false;
        });
        // 如果有子菜单匹配，父菜单不选中
        return !hasMatchingChild;
      }
      return true;
    }

    // 路径前缀匹配（只对没有子菜单的叶子节点）
    if (!item.children || item.children.length === 0) {
      if (pathname.startsWith(href + '/')) return true;
    }

    return false;
  };

  // 使用唯一标识符来管理展开状态（组合name和href，避免href为#时的冲突）
  const getItemKey = (item: NavItem, parentPath: string = '') => {
    return `${parentPath}-${item.name}-${item.href}`;
  };

  const toggleExpand = (itemKey: string) => {
    // 切换展开/折叠状态
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(itemKey)) {
        // 如果已展开，则折叠
        next.delete(itemKey);
        // 同时添加到折叠列表
        setCollapsedItems((prevCollapsed) => {
          const nextCollapsed = new Set(prevCollapsed);
          nextCollapsed.add(itemKey);
          return nextCollapsed;
        });
      } else {
        // 如果已折叠，则展开
        next.add(itemKey);
        // 从折叠列表中移除
        setCollapsedItems((prevCollapsed) => {
          const nextCollapsed = new Set(prevCollapsed);
          nextCollapsed.delete(itemKey);
          return nextCollapsed;
        });
      }
      return next;
    });
  };

  const isExpanded = (itemKey: string, item: NavItem) => {
    // 优先级1: 如果用户手动折叠了，强制折叠（最高优先级）
    if (collapsedItems.has(itemKey)) {
      return false;
    }

    // 优先级2: 如果用户手动展开过，保持展开状态
    if (expandedItems.has(itemKey)) {
      return true;
    }

    // 优先级3: 检查子菜单是否匹配当前路径（只有子菜单匹配时才自动展开）
    if (item.children && pathname) {
      for (const child of item.children) {
        // 精确匹配子菜单
        if (pathname === child.href) {
          return true;
        }
        // 路径以子菜单开头（处理嵌套路由）
        if (child.href && pathname.startsWith(child.href + '/')) {
          return true;
        }
        // 递归检查更深层的子菜单
        if (child.children) {
          for (const grandChild of child.children) {
            if (pathname === grandChild.href) {
              return true;
            }
            if (grandChild.href && pathname.startsWith(grandChild.href + '/')) {
              return true;
            }
          }
        }
      }
    }

    // 优先级4: 默认折叠状态（不自动展开）
    return false;
  };

  const renderNavItem = (item: NavItem, level: number = 0, parentPath: string = '') => {
    const hasChildren = item.children && item.children.length > 0;
    const active = isActive(item.href, item);
    // 使用唯一的key来管理展开状态
    const itemKey = getItemKey(item, parentPath);
    const expanded = isExpanded(itemKey, item);
    const indentClass = level > 0 ? `ml-${level * 6}` : '';
    // 使用唯一的key：组合父路径和当前项的名称
    const uniqueKey = `${parentPath}-${item.name}-${item.href}`;

    const IconComponent = typeof item.icon === 'string' ? null : item.icon;

    // 根据级别设置不同的颜色样式
    const getLevelStyles = (level: number, active: boolean) => {
      if (level === 0) {
        // 一级菜单
        return active
          ? 'bg-primary text-primary-foreground font-medium'
          : 'text-mutedForeground hover:bg-accent';
      } else if (level === 1) {
        // 二级菜单
        return active
          ? 'bg-primary/80 text-primary-foreground font-medium'
          : 'text-foreground hover:bg-accent/80';
      } else {
        // 三级及以上菜单
        return active
          ? 'bg-primary/60 text-primary-foreground font-medium'
          : 'text-mutedForeground hover:bg-accent/60';
      }
    };

    if (hasChildren) {
      return (
        <div key={uniqueKey} className={indentClass}>
          {level === 0 ? (
            <>
              <button
                onClick={() => toggleExpand(itemKey)}
                className="w-full flex items-center justify-between gap-3 px-4 py-3 text-mutedForeground font-medium hover:bg-accent rounded-lg transition-colors"
              >
                <div className="flex items-center gap-3">
                  {IconComponent ? (
                    <IconComponent className="w-5 h-5" />
                  ) : (
                    <span>{item.icon as string}</span>
                  )}
                  <span>{item.name}</span>
                </div>
                {expanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              {expanded && (
                <div className="mt-1 space-y-1">
                  {item.children?.map((child, index) => (
                    <div key={`${uniqueKey}-child-${index}`}>
                      {renderNavItem(child, level + 1, uniqueKey)}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleExpand(itemKey)}
                  className="flex-shrink-0 p-1 hover:bg-accent rounded transition-colors"
                >
                  {expanded ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                </button>
                <Link
                  href={item.href}
                  prefetch={true}
                  onClick={onClose}
                  className={`flex-1 flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${getLevelStyles(level, active)}`}
                >
                  {IconComponent && typeof IconComponent !== 'string' ? (
                    <IconComponent className="w-5 h-5" />
                  ) : (
                    <span className="text-xl">{item.icon as string}</span>
                  )}
                  <span>{item.name}</span>
                </Link>
              </div>
              {expanded && (
                <div className="mt-1 space-y-1 ml-6">
                  {item.children?.map((child, index) => (
                    <div key={`${uniqueKey}-child-${index}`}>
                      {renderNavItem(child, level + 1, uniqueKey)}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      );
    }

    return (
      <Link
        key={uniqueKey}
        href={item.href}
        prefetch={true}
        onClick={onClose}
        className={`${indentClass} flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${getLevelStyles(level, active)}`}
      >
        {IconComponent && typeof IconComponent !== 'string' ? (
          <IconComponent className="w-5 h-5" />
        ) : (
          <span className="text-xl">{item.icon as string}</span>
        )}
        <span>{item.name}</span>
      </Link>
    );
  };

  return (
    <>
      {/* 遮罩层（移动端） */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden" onClick={onClose} />
      )}

      {/* 侧边栏 */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo和关闭按钮 */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-border">
            <Link href="/" className="flex items-center gap-2">
              <img
                src="/logo.jpg"
                alt="中化国际"
                className="object-contain"
                style={{ maxHeight: '48px', height: 'auto', width: 'auto' }}
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </Link>
            <button
              onClick={onClose}
              className="lg:hidden text-mutedForeground hover:text-foreground focus:outline-none"
              aria-label="关闭菜单"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* 导航菜单 */}
          <nav className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
            {filterMenuByPermissions(adminNavigation).map((item, index) => (
              <div key={`nav-item-${index}-${item.name}`}>
                {renderNavItem(item, 0, `nav-${index}`)}
              </div>
            ))}
          </nav>

          {/* 用户信息（底部） */}
          {user && (
            <div className="border-t border-border p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-primary font-semibold">
                    {user.username?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{user.username}</p>
                  <p className="text-xs text-mutedForeground truncate">{user.email}</p>
                </div>
              </div>
              <Link
                href="/admin/settings"
                className="block w-full px-4 py-2 text-sm text-foreground hover:bg-accent rounded-lg transition-colors text-center"
                onClick={onClose}
              >
                个人设置
              </Link>
            </div>
          )}
        </div>
      </aside>
    </>
  );
});

