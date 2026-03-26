'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

const routeLabels: Record<string, string> = {
  '/': '首页',
  '/chat': 'AI助手',
  '/ai-scenarios': '场景库',
  '/workflow-designer': '工作流设计器',
  '/admin': '管理后台',
  '/admin/dashboard': '仪表板',
  '/admin/users': '用户管理',
  '/admin/workflows': '工作流管理',
  '/admin/tools': '工具管理',
  '/admin/monitoring': '系统监控',
  '/admin/monitoring/services': '服务监控',
  '/admin/monitoring/logs': '日志查看',
  '/admin/settings': '个人设置',
  '/projects': '项目管理',
  '/projects/dashboard': '项目仪表板',
  '/projects/tasks': '任务管理',
  '/projects/milestones': '里程碑',
  '/projects/phases': '项目阶段',
  '/projects/plans': '项目计划',
  '/projects/plans/templates': '计划模板',
  '/projects/risks': '风险管理',
  '/projects/weekly-reports': '周报',
  '/projects/monthly-reports': '月报',
  '/projects/reports': '报告管理',
  '/projects/import': '项目导入',
  '/projects/programs': '项目群管理',
  '/projects/programs/create': '创建项目群',
  '/projects/phase-statistics': '阶段统计',
  '/login': '登录',
};

// 单个路径段的中文映射（用于未在 routeLabels 中定义的路径）
const pathSegmentLabels: Record<string, string> = {
  'programs': '项目群管理',
  'create': '创建',
  'edit': '编辑',
  'dashboard': '仪表板',
  'tasks': '任务管理',
  'milestones': '里程碑',
  'phases': '项目阶段',
  'plans': '项目计划',
  'risks': '风险管理',
  'weekly-reports': '周报',
  'monthly-reports': '月报',
  'reports': '报告管理',
  'import': '项目导入',
  'phase-statistics': '阶段统计',
};

export function Breadcrumbs() {
  const pathname = usePathname();

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (!pathname) return [];

    const paths = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [{ label: '首页', href: '/' }];

    let currentPath = '';
    paths.forEach((path, index) => {
      currentPath += `/${path}`;

      // 检查是否是UUID格式（项目ID、计划ID等）
      const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(path);

      let label: string;
      if (routeLabels[currentPath]) {
        label = routeLabels[currentPath];
      } else if (isUUID) {
        // 如果是UUID，根据上一级路径推断实体类型（项目/场景等）
        const parent = paths[index - 1] || '';
        const nameKeyPrefix = parent === 'ai-scenarios' ? 'ai_scenario_name_' : 'project_name_';
        const fallbackLabel = parent === 'ai-scenarios' ? '场景详情' : '项目详情';
        const entityName =
          typeof window !== 'undefined'
            ? sessionStorage.getItem(`${nameKeyPrefix}${path}`) ||
              localStorage.getItem(`${nameKeyPrefix}${path}`)
            : null;
        label = entityName || fallbackLabel;
      } else if (pathSegmentLabels[path]) {
        // 如果路径段有中文映射，使用中文
        label = pathSegmentLabels[path];
      } else {
        // 默认使用原始路径，但可以尝试首字母大写
        label = path.charAt(0).toUpperCase() + path.slice(1).replace(/-/g, ' ');
      }

      const isLast = index === paths.length - 1;

      breadcrumbs.push({
        label: label,
        href: isLast ? undefined : currentPath,
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-between mb-4">
      <nav className="flex items-center space-x-2 text-sm text-gray-500" aria-label="面包屑导航">
        {breadcrumbs.map((item, index) => {
          const isLast = index === breadcrumbs.length - 1;

          return (
            <div key={index} className="flex items-center">
              {index > 0 && (
                <svg
                  className="w-4 h-4 mx-2 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              )}
              {item.href && !isLast ? (
                <Link href={item.href} className="hover:text-gray-700 transition-colors">
                  {item.label}
                </Link>
              ) : (
                <span className={isLast ? 'text-gray-900 font-medium' : ''}>{item.label}</span>
              )}
            </div>
          );
        })}
      </nav>
      <Link
        href="/portal"
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
        title="返回门户"
      >
        <Home className="h-5 w-5" />
        <span className="hidden sm:inline">返回门户</span>
      </Link>
    </div>
  );
}

