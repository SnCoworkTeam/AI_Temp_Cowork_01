'use client';

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { TreeNavigationView } from './TreeNavigationView';
import { GraphVisualizationView } from './GraphVisualizationView';
import { GripVertical, X, Info } from 'lucide-react';

interface MetadataItem {
  id: string | number;
  name: string;
  display_name?: string;
  description?: string;
  type?: string;
  parent_id?: string | number;
  [key: string]: any;
}

type MetadataType = 'all' | 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

interface HybridViewProps {
  items: MetadataItem[];
  type: MetadataType;
  onItemClick?: (item: MetadataItem) => void;
  loading?: boolean;
  emptyMessage?: string;
  defaultTreeWidth?: number;
  defaultGraphHeight?: number;
}

export function HybridView({
  items,
  type,
  onItemClick,
  loading = false,
  emptyMessage = '暂无数据',
  defaultTreeWidth = 300,
  defaultGraphHeight = 600,
}: HybridViewProps) {
  const [treeWidth, setTreeWidth] = useState(defaultTreeWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [selectedItem, setSelectedItem] = useState<MetadataItem | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  // 处理树节点点击 - 更新图谱显示
  const handleTreeItemClick = useCallback(
    (item: MetadataItem) => {
      setSelectedItem(item);
      setShowDetail(true);
      onItemClick?.(item);
    },
    [onItemClick]
  );

  // 处理图谱节点点击
  const handleGraphItemClick = useCallback(
    (item: MetadataItem) => {
      setSelectedItem(item);
      setShowDetail(true);
      onItemClick?.(item);
    },
    [onItemClick]
  );

  // 开始调整大小
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  // 调整大小
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = e.clientX;
      if (newWidth >= 200 && newWidth <= window.innerWidth - 200) {
        setTreeWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // 详情面板内容
  const detailContent = useMemo(() => {
    if (!selectedItem) return null;

    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">基本信息</h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium text-gray-700">名称：</span>
              <span className="text-gray-900">
                {selectedItem.display_name || selectedItem.name}
              </span>
            </div>
            {selectedItem.type && (
              <div>
                <span className="font-medium text-gray-700">类型：</span>
                <span className="text-gray-900">{selectedItem.type}</span>
              </div>
            )}
            {selectedItem.description && (
              <div>
                <span className="font-medium text-gray-700">描述：</span>
                <span className="text-gray-900">{selectedItem.description}</span>
              </div>
            )}
            {selectedItem.status && (
              <div>
                <span className="font-medium text-gray-700">状态：</span>
                <span className="text-gray-900">{selectedItem.status}</span>
              </div>
            )}
          </div>
        </div>

        {selectedItem.metadata && Object.keys(selectedItem.metadata).length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">元数据</h3>
            <div className="bg-gray-50 rounded-lg p-3 text-xs">
              <pre className="text-gray-700 overflow-x-auto">
                {JSON.stringify(selectedItem.metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  }, [selectedItem]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <Info className="w-12 h-12 mb-4 text-gray-400" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* 树形导航面板 */}
      <div
        className="bg-white border-r border-gray-200 overflow-y-auto"
        style={{ width: `${treeWidth}px`, minWidth: '200px', maxWidth: '50%' }}
      >
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">导航树</h3>
          <TreeNavigationView
            items={items}
            type={type}
            onItemClick={handleTreeItemClick}
            loading={false}
            emptyMessage={emptyMessage}
          />
        </div>
      </div>

      {/* 调整大小的拖拽条 */}
      <div
        className="w-1 bg-gray-200 hover:bg-blue-500 cursor-col-resize transition-colors relative group"
        onMouseDown={handleMouseDown}
      >
        <div className="absolute inset-y-0 left-1/2 transform -translate-x-1/2 w-8 flex items-center justify-center">
          <GripVertical className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
        </div>
      </div>

      {/* 图谱可视化面板 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <GraphVisualizationView
            items={items}
            type={type}
            onItemClick={handleGraphItemClick}
            loading={false}
            emptyMessage={emptyMessage}
            height={defaultGraphHeight}
          />
        </div>
      </div>

      {/* 详情面板 */}
      {showDetail && selectedItem && (
        <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">详情</h3>
              <button
                onClick={() => {
                  setShowDetail(false);
                  setSelectedItem(null);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            {detailContent}
          </div>
        </div>
      )}
    </div>
  );
}
