'use client';

import { useState, useEffect } from 'react';
import { Menu, Edit, Save, X, Search, Shield, Key, ChevronRight, ChevronDown } from 'lucide-react';
import { getMenuConfig, saveMenuConfig as saveMenuConfigApi, MenuConfigItem } from '@/lib/api/admin';

interface MenuPermissionConfig {
  name: string;
  href: string;
  requiredPermission?: string;
  requireAdmin?: boolean;
  children?: MenuPermissionConfig[];
}

// 从 Sidebar 提取的完整菜单结构
const defaultMenuStructure: MenuPermissionConfig[] = [
  {
    name: '仪表板',
    href: '/dashboard',
  },
  {
    name: '个人工作',
    href: '#',
    children: [
      { name: '待办事项', href: '/todos' },
      { name: '通知中心', href: '/notifications' },
      { name: '个人工作台', href: '/workspace' },
      { name: '收藏夹', href: '/favorites' },
    ],
  },
  {
    name: '业务管理',
    href: '#',
    children: [
      {
        name: '项目管理',
        href: '/projects',
        children: [
          { name: '仪表盘', href: '/projects/dashboard' },
          { name: '项目列表', href: '/projects' },
          { name: '创建项目', href: '/projects/create' },
          { name: '计划模板', href: '/projects/plans/templates' },
          { name: '进度计划', href: '/projects/schedule' },
          { name: '项目导入', href: '/projects/import' },
          { name: '阶段统计', href: '/projects/phase-statistics' },
          { name: '任务管理', href: '/projects/tasks' },
          { name: '周报管理', href: '/projects/weekly-reports' },
          { name: '月报管理', href: '/projects/monthly-reports' },
          { name: '周月进度报告', href: '/projects/progress-reports' },
          { name: '报告管理', href: '/projects/reports' },
          { name: '风险管理', href: '/projects/risks' },
          { name: '基础数据维护', href: '/projects/basic-data' },
        ],
      },
    ],
  },
  {
    name: 'AI智能',
    href: '#',
    children: [
      { name: 'AI助手', href: '/chat' },
      { name: '智能体', href: '/agents' },
      { name: '知识库', href: '/knowledge-bases' },
      { name: '知识图谱', href: '/knowledge-graph' },
      { name: '对话历史', href: '/conversations' },
    ],
  },
  {
    name: '工作流',
    href: '#',
    children: [
      { name: '工作流列表', href: '/workflows' },
      { name: '工作流设计器', href: '/workflow-designer' },
    ],
  },
  {
    name: '企业架构',
    href: '#',
    children: [
      { name: '总览', href: '/enterprise-architecture' },
      { name: '组织架构', href: '/enterprise-architecture/organization' },
      { name: '业务架构', href: '/enterprise-architecture/business' },
      { name: '应用架构', href: '/enterprise-architecture/application' },
      { name: '数据架构', href: '/enterprise-architecture/data' },
      { name: '技术架构', href: '/enterprise-architecture/technology' },
      { name: '技术实例', href: '/enterprise-architecture/technology/instances' },
      { name: '技术标准化', href: '/enterprise-architecture/technology/standardization' },
      { name: '架构关系图', href: '/enterprise-architecture/relationships' },
    ],
  },
  {
    name: '系统管理',
    href: '#',
    requireAdmin: true,
    children: [
      {
        name: '权限管理',
        href: '/admin/permissions',
        requireAdmin: true,
        children: [
          { name: '用户管理', href: '/admin/permissions/users', requireAdmin: true },
          { name: '角色管理', href: '/admin/permissions/roles', requireAdmin: true },
          { name: '权限管理', href: '/admin/permissions/permissions', requireAdmin: true },
          { name: '菜单权限', href: '/admin/permissions/menus', requireAdmin: true },
        ],
      },
      { name: '工作流管理', href: '/admin/workflows', requireAdmin: true },
      { name: '工具管理', href: '/admin/tools', requireAdmin: true },
      {
        name: '提示词管理',
        href: '/admin/prompts',
        requireAdmin: true,
        children: [
          { name: '提示词列表', href: '/admin/prompts', requireAdmin: true },
          { name: '创建提示词', href: '/admin/prompts/create', requireAdmin: true },
        ],
      },
      { name: '元数据管理', href: '/admin/metadata', requireAdmin: true },
      {
        name: '系统监控',
        href: '/admin/monitoring',
        requireAdmin: true,
        children: [
          { name: '监控总览', href: '/admin/monitoring', requireAdmin: true },
          { name: '服务监控', href: '/admin/monitoring/services', requireAdmin: true },
          { name: '日志查看', href: '/admin/monitoring/logs', requireAdmin: true },
          { name: '自动调试', href: '/admin/auto-debug/decision-panel', requireAdmin: true },
        ],
      },
      {
        name: '数据库管理',
        href: '/admin/database/overview',
        requireAdmin: true,
        children: [
          { name: '数据库概览', href: '/admin/database/overview', requireAdmin: true },
          { name: '表管理', href: '/admin/database/tables', requireAdmin: true },
          { name: '性能监控', href: '/admin/database/performance', requireAdmin: true },
          { name: '备份管理', href: '/admin/database/backups', requireAdmin: true },
          { name: '图数据库', href: '/admin/database/neo4j', requireAdmin: true },
          { name: 'Neo4j图谱', href: '/neo4j-graph', requireAdmin: true },
        ],
      },
    ],
  },
  {
    name: '其他',
    href: '#',
    children: [
      { name: '组件库', href: '/components' },
      { name: '帮助中心', href: '/help' },
      { name: '系统公告', href: '/announcements' },
      { name: '数据看板', href: '/data-dashboard' },
    ],
  },
];

export default function MenuPermissionsPage() {
  const [menuConfig, setMenuConfig] = useState<MenuPermissionConfig[]>([]);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMenuConfig();
  }, []);

  const loadMenuConfig = async () => {
    try {
      setLoading(true);
      const response = await getMenuConfig();
      const config = response?.config;
      if (Array.isArray(config) && config.length > 0) {
        setMenuConfig(config as MenuPermissionConfig[]);
      } else {
        setMenuConfig(defaultMenuStructure);
      }
    } catch (error) {
      console.error('加载菜单配置失败:', error);
      setMenuConfig(defaultMenuStructure);
    } finally {
      setLoading(false);
    }
  };

  const saveMenuConfig = async () => {
    try {
      await saveMenuConfigApi(menuConfig as MenuConfigItem[]);
      alert('菜单权限配置已保存！');
    } catch (error) {
      console.error('保存菜单配置失败:', error);
      alert('保存失败，请重试');
    }
  };

  const toggleExpand = (path: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedItems(newExpanded);
  };

  const updateMenuItem = (
    items: MenuPermissionConfig[],
    targetPath: string,
    updates: Partial<MenuPermissionConfig>
  ): MenuPermissionConfig[] => {
    return items.map((item) => {
      if (item.href === targetPath) {
        return { ...item, ...updates };
      }
      if (item.children) {
        return {
          ...item,
          children: updateMenuItem(item.children, targetPath, updates),
        };
      }
      return item;
    });
  };

  const handleEdit = (item: MenuPermissionConfig) => {
    setEditingItem(item.href);
  };

  const handleSave = (item: MenuPermissionConfig, updates: Partial<MenuPermissionConfig>) => {
    const updated = updateMenuItem(menuConfig, item.href, updates);
    setMenuConfig(updated);
    setEditingItem(null);
  };

  const handleCancel = () => {
    setEditingItem(null);
  };

  const filterMenuItems = (items: MenuPermissionConfig[]): MenuPermissionConfig[] => {
    if (!searchTerm) return items;

    return items
      .filter((item) => {
        const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
        const childrenMatch = item.children ? filterMenuItems(item.children).length > 0 : false;
        return matchesSearch || childrenMatch;
      })
      .map((item) => ({
        ...item,
        children: item.children ? filterMenuItems(item.children) : undefined,
      }));
  };

  const renderMenuItem = (
    item: MenuPermissionConfig,
    level: number = 0,
    path: string = '',
    index: number = 0
  ) => {
    // currentPath用于展开/收起功能
    const currentPath = path ? `${path}.${item.href}` : item.href;
    // uniqueKey用于React key，确保唯一性
    const uniqueKey = `${item.name}-${item.href}-${index}-${level}-${path}`;
    const isExpanded = expandedItems.has(currentPath);
    const isEditing = editingItem === item.href;
    const hasChildren = item.children && item.children.length > 0;
    const filteredChildren = item.children ? filterMenuItems(item.children) : [];

    return (
      <div key={uniqueKey} className="border-b border-gray-200 last:border-b-0">
        <div
          className={`flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors ${
            level > 0 ? 'bg-gray-50' : ''
          }`}
          style={{ paddingLeft: `${level * 24 + 16}px` }}
        >
          {/* 展开/收起按钮 */}
          {hasChildren && (
            <button
              onClick={() => toggleExpand(currentPath)}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-600" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-600" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-6" />}

          {/* 菜单图标 */}
          <Menu className="w-5 h-5 text-gray-400 flex-shrink-0" />

          {/* 菜单名称和路径 */}
          <div className="flex-1 min-w-0">
            <div className="font-medium text-gray-900">{item.name}</div>
            <div className="text-sm text-gray-500 truncate">{item.href}</div>
          </div>

          {/* 权限配置显示/编辑 */}
          {isEditing ? (
            <MenuItemEditor
              item={item}
              onSave={(updates) => handleSave(item, updates)}
              onCancel={handleCancel}
            />
          ) : (
            <div className="flex items-center gap-4">
              {/* 权限代码 */}
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-600">{item.requiredPermission || '无'}</span>
              </div>

              {/* 管理员权限 */}
              {item.requireAdmin && (
                <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                  <Shield className="w-3 h-3" />
                  管理员
                </div>
              )}

              {/* 编辑按钮 */}
              <button
                onClick={() => handleEdit(item)}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                title="编辑权限配置"
              >
                <Edit className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* 子菜单 */}
        {hasChildren && isExpanded && (
          <div className="bg-gray-50">
            {filteredChildren.map((child, idx) =>
              renderMenuItem(child, level + 1, currentPath, idx)
            )}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const filteredMenus = filterMenuItems(menuConfig);

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">菜单权限管理</h1>
          <p className="text-gray-600 mt-1">配置系统菜单项的访问权限，控制不同角色用户可见的菜单</p>
        </div>
        <button
          onClick={saveMenuConfig}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Save className="w-4 h-4" />
          保存配置
        </button>
      </div>

      {/* 搜索框 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="搜索菜单项..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* 菜单列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="divide-y divide-gray-200">
          {filteredMenus.length > 0 ? (
            filteredMenus.map((item, idx) => renderMenuItem(item, 0, '', idx))
          ) : (
            <div className="p-8 text-center text-gray-500">没有找到匹配的菜单项</div>
          )}
        </div>
      </div>

      {/* 说明信息 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">配置说明</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            • <strong>权限代码</strong>：设置访问该菜单项所需的权限代码（如：project:read）
          </li>
          <li>
            • <strong>管理员权限</strong>：勾选后，只有管理员角色可以访问该菜单项
          </li>
          <li>
            • <strong>继承关系</strong>：子菜单会继承父菜单的权限要求
          </li>
          <li>
            • <strong>保存配置</strong>：配置会保存到浏览器本地存储，刷新页面后生效
          </li>
        </ul>
      </div>
    </div>
  );
}

// 菜单项编辑器组件
function MenuItemEditor({
  item,
  onSave,
  onCancel,
}: {
  item: MenuPermissionConfig;
  onSave: (updates: Partial<MenuPermissionConfig>) => void;
  onCancel: () => void;
}) {
  const [permissionCode, setPermissionCode] = useState(item.requiredPermission || '');
  const [requireAdmin, setRequireAdmin] = useState(item.requireAdmin || false);

  const handleSave = () => {
    onSave({
      requiredPermission: permissionCode || undefined,
      requireAdmin: requireAdmin || undefined,
    });
  };

  return (
    <div className="flex items-center gap-2 bg-white border border-blue-300 rounded-lg p-2 shadow-lg">
      <div className="flex items-center gap-2">
        <Key className="w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={permissionCode}
          onChange={(e) => setPermissionCode(e.target.value)}
          placeholder="权限代码（可选）"
          className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-48"
        />
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={requireAdmin}
          onChange={(e) => setRequireAdmin(e.target.checked)}
          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <span className="text-sm text-gray-700">管理员</span>
      </label>

      <button
        onClick={handleSave}
        className="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors"
        title="保存"
      >
        <Save className="w-4 h-4" />
      </button>

      <button
        onClick={onCancel}
        className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
        title="取消"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

