'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Search,
  Filter,
  Folder,
  FolderOpen,
  FileText,
} from 'lucide-react';

interface MetadataItem {
  id: string | number;
  name: string;
  display_name?: string;
  description?: string;
  type?: string;
  parent_id?: string | number;
  level?: number;
  children?: MetadataItem[];
  [key: string]: any;
}

type MetadataType = 'all' | 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

interface TreeNavigationViewProps {
  items: MetadataItem[];
  type: MetadataType;
  onItemClick?: (item: MetadataItem) => void;
  loading?: boolean;
  emptyMessage?: string;
  enableSearch?: boolean;
  enableFilter?: boolean;
  lazyLoad?: boolean;
  onLoadChildren?: (item: MetadataItem) => Promise<MetadataItem[]>;
}

interface TreeNode {
  item: MetadataItem;
  children: TreeNode[];
  expanded: boolean;
  loaded: boolean;
  level: number;
}

export function TreeNavigationView({
  items,
  type,
  onItemClick,
  loading = false,
  emptyMessage = '暂无数据',
  enableSearch = true,
  enableFilter = true,
  lazyLoad = false,
  onLoadChildren,
}: TreeNavigationViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedNodes, setExpandedNodes] = useState<Set<string | number>>(new Set());
  const [loadingNodes, setLoadingNodes] = useState<Set<string | number>>(new Set());
  const [filterType, setFilterType] = useState<string>('all');

  // 构建树形结构
  const buildTree = useCallback(
    (items: MetadataItem[]): TreeNode[] => {
      // 创建映射
      const itemMap = new Map<string | number, MetadataItem>();
      const rootItems: MetadataItem[] = [];

      // 第一遍：创建映射并找出根节点
      items.forEach((item) => {
        itemMap.set(item.id, item);
        if (!item.parent_id) {
          rootItems.push(item);
        }
      });

      // 第二遍：构建父子关系
      items.forEach((item) => {
        if (item.parent_id && itemMap.has(item.parent_id)) {
          const parent = itemMap.get(item.parent_id)!;
          if (!parent.children) {
            parent.children = [];
          }
          parent.children.push(item);
        }
      });

      // 递归构建树节点
      const buildTreeNode = (item: MetadataItem, level: number = 0): TreeNode => {
        const children = item.children || [];
        return {
          item,
          children: children.map((child) => buildTreeNode(child, level + 1)),
          expanded: expandedNodes.has(item.id),
          loaded: !lazyLoad || children.length > 0,
          level,
        };
      };

      return rootItems.map((item) => buildTreeNode(item));
    },
    [expandedNodes, lazyLoad]
  );

  // 过滤和搜索
  const filteredItems = useMemo(() => {
    let filtered = items;

    // 按类型过滤
    if (filterType !== 'all') {
      filtered = filtered.filter(
        (item) => item.type === filterType || item.asset_type === filterType
      );
    }

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((item) => {
        const name = (item.display_name || item.name || '').toLowerCase();
        const desc = (item.description || '').toLowerCase();
        return name.includes(query) || desc.includes(query);
      });
    }

    return filtered;
  }, [items, searchQuery, filterType]);

  // 构建树
  const tree = useMemo(() => buildTree(filteredItems), [filteredItems, buildTree]);

  // 获取所有类型（用于筛选）
  const allTypes = useMemo(() => {
    const types = new Set<string>();
    items.forEach((item) => {
      if (item.type) types.add(item.type);
      if (item.asset_type) types.add(item.asset_type);
    });
    return Array.from(types).sort();
  }, [items]);

  // 切换节点展开/折叠
  const toggleNode = useCallback(
    async (node: TreeNode) => {
      const nodeId = node.item.id;

      // 懒加载子节点
      if (lazyLoad && !node.loaded && onLoadChildren) {
        setLoadingNodes((prev) => new Set(prev).add(nodeId));
        try {
          const children = await onLoadChildren(node.item);
          // 更新节点数据（这里需要父组件支持数据更新）
          setLoadingNodes((prev) => {
            const next = new Set(prev);
            next.delete(nodeId);
            return next;
          });
        } catch (error) {
          console.error('Failed to load children:', error);
          setLoadingNodes((prev) => {
            const next = new Set(prev);
            next.delete(nodeId);
            return next;
          });
        }
      }

      // 切换展开状态
      setExpandedNodes((prev) => {
        const next = new Set(prev);
        if (next.has(nodeId)) {
          next.delete(nodeId);
        } else {
          next.add(nodeId);
        }
        return next;
      });
    },
    [lazyLoad, onLoadChildren]
  );

  // 渲染树节点
  const renderTreeNode = useCallback(
    (node: TreeNode) => {
      const hasChildren = node.children.length > 0 || (lazyLoad && !node.loaded);
      const isExpanded = expandedNodes.has(node.item.id);
      const isLoading = loadingNodes.has(node.item.id);

      return (
        <div key={node.item.id} className="select-none">
          <div
            className={`
            flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 cursor-pointer
            ${node.level > 0 ? 'ml-4' : ''}
          `}
            style={{ paddingLeft: `${node.level * 1.5 + 0.5}rem` }}
            onClick={() => {
              if (hasChildren) {
                toggleNode(node);
              }
              onItemClick?.(node.item);
            }}
          >
            {/* 展开/折叠图标 */}
            <div className="w-4 h-4 flex items-center justify-center">
              {hasChildren ? (
                isLoading ? (
                  <div className="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                ) : isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                )
              ) : (
                <div className="w-4 h-4" />
              )}
            </div>

            {/* 节点图标 */}
            <div className="flex-shrink-0">
              {hasChildren ? (
                isExpanded ? (
                  <FolderOpen className="w-4 h-4 text-blue-500" />
                ) : (
                  <Folder className="w-4 h-4 text-gray-400" />
                )
              ) : (
                <FileText className="w-4 h-4 text-gray-400" />
              )}
            </div>

            {/* 节点内容 */}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-900 truncate">
                {node.item.display_name || node.item.name}
              </div>
              {node.item.description && (
                <div className="text-xs text-gray-500 truncate">{node.item.description}</div>
              )}
            </div>

            {/* 节点标签 */}
            {node.item.type && (
              <span className="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-800">
                {node.item.type}
              </span>
            )}
          </div>

          {/* 子节点 */}
          {isExpanded && node.children.length > 0 && (
            <div>{node.children.map((child) => renderTreeNode(child))}</div>
          )}
        </div>
      );
    },
    [expandedNodes, loadingNodes, toggleNode, onItemClick, lazyLoad]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  if (tree.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <FileText className="w-12 h-12 mb-4 text-gray-400" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 搜索和筛选工具栏 */}
      {(enableSearch || enableFilter) && (
        <div className="flex gap-2">
          {enableSearch && (
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
          )}
          {enableFilter && allTypes.length > 0 && (
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white text-sm"
              >
                <option value="all">全部分类</option>
                {allTypes.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* 树形结构 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 max-h-[600px] overflow-y-auto">
        {tree.map((node) => renderTreeNode(node))}
      </div>
    </div>
  );
}
