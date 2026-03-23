'use client';

import React, { useState, useEffect } from 'react';
import { CardGridView } from './CardGridView';
import { EnhancedListView } from './EnhancedListView';
import { TreeNavigationView } from './TreeNavigationView';
import { GraphVisualizationView } from './GraphVisualizationView';
import { HybridView } from './HybridView';
import { EditableTableView } from './EditableTableView';
import { List, LayoutGrid, Network, GitBranch, Table } from 'lucide-react';

type ViewMode = 'grid' | 'list' | 'tree' | 'graph' | 'hybrid' | 'table';

interface MetadataItem {
  id: string | number;
  name: string;
  display_name?: string;
  description?: string;
  type?: string;
  asset_type?: string;
  status?: string;
  classification?: string;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  [key: string]: any;
}

type MetadataType = 'all' | 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

interface MetadataViewEngineProps {
  items: MetadataItem[];
  type: MetadataType;
  onItemClick?: (item: MetadataItem) => void;
  loading?: boolean;
  emptyMessage?: string;
  defaultView?: ViewMode;
  showViewToggle?: boolean;
}

// 从localStorage加载用户偏好
const loadViewPreference = (type: MetadataType): ViewMode => {
  if (typeof window === 'undefined') return 'grid';

  try {
    const key = `metadata_view_${type}`;
    const saved = localStorage.getItem(key);
    if (
      saved === 'grid' ||
      saved === 'list' ||
      saved === 'tree' ||
      saved === 'graph' ||
      saved === 'hybrid' ||
      saved === 'table'
    ) {
      return saved as ViewMode;
    }
  } catch (error) {
    console.warn('[MetadataViewEngine] Failed to load view preference:', error);
  }

  return 'grid';
};

// 保存用户偏好到localStorage
const saveViewPreference = (type: MetadataType, view: ViewMode) => {
  if (typeof window === 'undefined') return;

  try {
    const key = `metadata_view_${type}`;
    localStorage.setItem(key, view);
  } catch (error) {
    console.warn('[MetadataViewEngine] Failed to save view preference:', error);
  }
};

// 场景判断：根据数据特征自动推荐视图
const recommendView = (items: MetadataItem[], type: MetadataType): ViewMode => {
  // 如果数据包含层级关系（有parent_id），推荐树形视图或混合视图
  const hasHierarchy = items.some(
    (item) => item.parent_id !== undefined && item.parent_id !== null
  );
  if (hasHierarchy && items.length > 5) {
    return 'hybrid'; // 混合视图：树形+图谱
  }

  // 如果数据量很大（>100），推荐列表视图或表格视图（性能更好）
  if (items.length > 100) {
    return 'table';
  }

  // 如果数据包含大量描述性信息，推荐卡片视图（展示更丰富）
  const itemsWithDescription = items.filter(
    (item) => item.description && item.description.length > 50
  );
  if (itemsWithDescription.length > items.length * 0.5) {
    return 'grid';
  }

  // 默认使用网格视图
  return 'grid';
};

export function MetadataViewEngine({
  items,
  type,
  onItemClick,
  loading = false,
  emptyMessage = '暂无数据',
  defaultView,
  showViewToggle = true,
}: MetadataViewEngineProps) {
  // 初始化视图：优先使用用户偏好，其次使用推荐视图，最后使用默认值
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    if (defaultView) return defaultView;
    const preference = loadViewPreference(type);
    if (preference) return preference;
    return recommendView(items, type);
  });

  // 当类型变化时，加载对应的用户偏好
  useEffect(() => {
    const preference = loadViewPreference(type);
    if (preference) {
      setViewMode(preference);
    } else {
      // 如果没有偏好，使用推荐视图
      const recommended = recommendView(items, type);
      setViewMode(recommended);
    }
  }, [type, items.length]);

  // 切换视图并保存偏好
  const handleViewToggle = (newView: ViewMode) => {
    setViewMode(newView);
    saveViewPreference(type, newView);
  };

  return (
    <div className="space-y-4">
      {/* 视图切换按钮 */}
      {showViewToggle && (
        <div className="flex items-center justify-end gap-2 bg-white rounded-lg border border-gray-200 p-2">
          <span className="text-sm text-gray-600 mr-2">视图:</span>
          <div className="flex items-center gap-1 border border-gray-300 rounded">
            <button
              onClick={() => handleViewToggle('grid')}
              className={`
                px-3 py-1.5 text-sm font-medium transition-colors
                ${
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
              title="网格视图"
            >
              <LayoutGrid className="w-4 h-4 inline-block mr-1" />
              网格
            </button>
            <button
              onClick={() => handleViewToggle('list')}
              className={`
                px-3 py-1.5 text-sm font-medium transition-colors
                ${
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
              title="列表视图"
            >
              <List className="w-4 h-4 inline-block mr-1" />
              列表
            </button>
            <button
              onClick={() => handleViewToggle('tree')}
              className={`
                px-3 py-1.5 text-sm font-medium transition-colors
                ${
                  viewMode === 'tree'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
              title="树形视图"
            >
              <Network className="w-4 h-4 inline-block mr-1" />
              树形
            </button>
            <button
              onClick={() => handleViewToggle('graph')}
              className={`
                px-3 py-1.5 text-sm font-medium transition-colors
                ${
                  viewMode === 'graph'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
              title="图谱视图"
            >
              <GitBranch className="w-4 h-4 inline-block mr-1" />
              图谱
            </button>
            <button
              onClick={() => handleViewToggle('hybrid')}
              className={`
                px-3 py-1.5 text-sm font-medium transition-colors
                ${
                  viewMode === 'hybrid'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
              title="混合视图"
            >
              <LayoutGrid className="w-4 h-4 inline-block mr-1" />
              混合
            </button>
            <button
              onClick={() => handleViewToggle('table')}
              className={`
                px-3 py-1.5 text-sm font-medium transition-colors
                ${
                  viewMode === 'table'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
              title="表格视图"
            >
              <Table className="w-4 h-4 inline-block mr-1" />
              表格
            </button>
          </div>
        </div>
      )}

      {/* 根据视图模式渲染对应组件 */}
      {viewMode === 'grid' ? (
        <CardGridView
          items={items}
          type={type}
          onItemClick={onItemClick}
          loading={loading}
          emptyMessage={emptyMessage}
        />
      ) : viewMode === 'list' ? (
        <EnhancedListView
          items={items}
          type={type}
          onItemClick={onItemClick}
          loading={loading}
          emptyMessage={emptyMessage}
        />
      ) : viewMode === 'tree' ? (
        <TreeNavigationView
          items={items}
          type={type}
          onItemClick={onItemClick}
          loading={loading}
          emptyMessage={emptyMessage}
        />
      ) : viewMode === 'graph' ? (
        <GraphVisualizationView
          items={items}
          type={type}
          onItemClick={onItemClick}
          loading={loading}
          emptyMessage={emptyMessage}
        />
      ) : viewMode === 'hybrid' ? (
        <HybridView
          items={items}
          type={type}
          onItemClick={onItemClick}
          loading={loading}
          emptyMessage={emptyMessage}
        />
      ) : (
        <EditableTableView
          items={items}
          type={type}
          onItemClick={onItemClick}
          loading={loading}
          emptyMessage={emptyMessage}
        />
      )}
    </div>
  );
}
