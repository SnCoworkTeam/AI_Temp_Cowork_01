'use client';

import React, { useRef, useCallback, useEffect, useState, useMemo, forwardRef } from 'react';
import dynamic from 'next/dynamic';
import { ZoomIn, ZoomOut, Search, Filter, X, Info, Maximize2, Minimize2 } from 'lucide-react';

// 动态导入以避免SSR问题
// react-force-graph 导出 ForceGraph2D 作为命名导出
// 使用 forwardRef 包装以支持 ref 传递
const ForceGraph2DBase = dynamic(
  () => import('react-force-graph').then((mod) => mod.ForceGraph2D),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full">加载图谱可视化组件...</div>
    ),
  }
);

// 使用 forwardRef 包装动态导入的组件以支持 ref
const ForceGraph2D = forwardRef<any, any>((props, ref) => {
  return <ForceGraph2DBase ref={ref} {...props} />;
});
ForceGraph2D.displayName = 'ForceGraph2D';

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

interface GraphVisualizationViewProps {
  items: MetadataItem[];
  type: MetadataType;
  onItemClick?: (item: MetadataItem) => void;
  loading?: boolean;
  emptyMessage?: string;
  height?: number;
}

interface GraphNode {
  id: string | number;
  name: string;
  type?: string;
  group?: string;
  metadata?: MetadataItem;
}

interface GraphLink {
  source: string | number;
  target: string | number;
  type?: string;
  value?: number;
}

export function GraphVisualizationView({
  items,
  type,
  onItemClick,
  loading = false,
  emptyMessage = '暂无数据',
  height = 600,
}: GraphVisualizationViewProps) {
  const graphRef = useRef<any>(null);
  const [mounted, setMounted] = useState(false);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showNodeDetail, setShowNodeDetail] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedPath, setHighlightedPath] = useState<Set<string | number>>(new Set());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    setMounted(true);
  }, []);

  // 构建图谱数据
  const graphData = useMemo(() => {
    if (!items || items.length === 0) {
      return { nodes: [], links: [] };
    }

    // 过滤数据
    let filteredItems = items;
    if (filterType !== 'all') {
      filteredItems = filteredItems.filter(
        (item) => item.type === filterType || item.asset_type === filterType
      );
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filteredItems = filteredItems.filter((item) => {
        const name = (item.display_name || item.name || '').toLowerCase();
        const desc = (item.description || '').toLowerCase();
        return name.includes(query) || desc.includes(query);
      });
    }

    // 构建节点
    const nodes: GraphNode[] = filteredItems.map((item) => ({
      id: item.id,
      name: item.display_name || item.name,
      type: item.type || item.asset_type,
      group: item.type || item.asset_type || 'default',
      metadata: item,
    }));

    // 构建边（基于parent_id关系）
    const links: GraphLink[] = [];
    const itemMap = new Map<string | number, MetadataItem>();
    filteredItems.forEach((item) => itemMap.set(item.id, item));

    filteredItems.forEach((item) => {
      if (item.parent_id && itemMap.has(item.parent_id)) {
        links.push({
          source: item.parent_id,
          target: item.id,
          type: 'parent_of',
          value: 1,
        });
      }
    });

    return { nodes, links };
  }, [items, searchQuery, filterType]);

  // 获取所有类型（用于筛选）
  const allTypes = useMemo(() => {
    const types = new Set<string>();
    items.forEach((item) => {
      if (item.type) types.add(item.type);
      if (item.asset_type) types.add(item.asset_type);
    });
    return Array.from(types).sort();
  }, [items]);

  // 节点颜色映射
  const getNodeColor = useCallback((node: GraphNode) => {
    const type = node.group || node.type || 'default';
    const colorMap: { [key: string]: string } = {
      workflow: '#1890ff',
      'ai-model': '#52c41a',
      'data-asset': '#fa8c16',
      'business-entity': '#722ed1',
      default: '#8c8c8c',
    };
    return colorMap[type] || colorMap['default'];
  }, []);

  // 节点大小计算
  const getNodeSize = useCallback(
    (node: GraphNode) => {
      const baseSize = 8;
      const connections = graphData.links.filter(
        (link) => link.source === node.id || link.target === node.id
      ).length;
      return baseSize + Math.min(connections * 2, 12);
    },
    [graphData.links]
  );

  // 处理节点点击
  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      setSelectedNode(node);
      setShowNodeDetail(true);

      // 高亮路径：找到从根节点到当前节点的路径
      const path = new Set<string | number>();
      const findPath = (nodeId: string | number, visited: Set<string | number> = new Set()) => {
        if (visited.has(nodeId)) return;
        visited.add(nodeId);
        path.add(nodeId);

        // 找到父节点
        const link = graphData.links.find((l) => l.target === nodeId);
        if (link) {
          findPath(link.source as string | number, visited);
        }
      };
      findPath(node.id);
      setHighlightedPath(path);

      onItemClick?.(node.metadata!);
    },
    [graphData.links, onItemClick]
  );

  // 处理节点悬停
  const handleNodeHover = useCallback((node: GraphNode | null) => {
    setHoveredNode(node);
  }, []);

  // 缩放控制
  const handleZoomIn = useCallback(() => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom() || 1;
      graphRef.current.zoom(currentZoom * 1.2);
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom() || 1;
      graphRef.current.zoom(currentZoom * 0.8);
    }
  }, []);

  const handleFitView = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 20);
    }
  }, []);

  // 切换全屏
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen((prev) => !prev);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  if (!graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <Info className="w-12 h-12 mb-4 text-gray-400" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-2">
        <div className="flex items-center gap-2">
          {/* 搜索 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索节点..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm w-48"
            />
          </div>

          {/* 类型筛选 */}
          {allTypes.length > 0 && (
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="pl-10 pr-8 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white text-sm"
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

        <div className="flex items-center gap-2">
          {/* 缩放控制 */}
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="放大"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="缩小"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleFitView}
            className="px-3 py-1.5 text-sm hover:bg-gray-100 rounded-lg transition-colors"
            title="适应视图"
          >
            适应视图
          </button>
          <button
            onClick={toggleFullscreen}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={isFullscreen ? '退出全屏' : '全屏'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* 图谱容器 */}
      <div
        className="bg-white rounded-lg border border-gray-200 relative overflow-hidden"
        style={{ height: isFullscreen ? 'calc(100vh - 120px)' : `${height}px` }}
      >
        {ForceGraph2D && mounted && (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeLabel={(node: GraphNode) => {
              return `${node.name}${node.type ? ` (${node.type})` : ''}`;
            }}
            nodeColor={(node: GraphNode) => {
              // 高亮选中的节点和路径
              if (selectedNode && selectedNode.id === node.id) {
                return '#ff4d4f';
              }
              if (highlightedPath.has(node.id)) {
                return '#faad14';
              }
              return getNodeColor(node);
            }}
            linkColor={(link: GraphLink) => {
              // 高亮路径中的边
              if (
                highlightedPath.has(link.source as string | number) &&
                highlightedPath.has(link.target as string | number)
              ) {
                return 'rgba(250, 173, 20, 0.8)';
              }
              return 'rgba(0, 0, 0, 0.2)';
            }}
            linkWidth={(link: GraphLink) => {
              if (
                highlightedPath.has(link.source as string | number) &&
                highlightedPath.has(link.target as string | number)
              ) {
                return 3;
              }
              return 2;
            }}
            nodeVal={(node: GraphNode) => getNodeSize(node)}
            nodeRelSize={6}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.25}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            onNodeDragEnd={(node: GraphNode) => {
              node.fx = node.x;
              node.fy = node.y;
            }}
            nodeCanvasObject={(
              node: GraphNode,
              ctx: CanvasRenderingContext2D,
              globalScale: number
            ) => {
              const label = node.name;
              const fontSize = Math.max(12 / Math.sqrt(globalScale), 10);
              ctx.font = `bold ${fontSize}px "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';

              // 绘制文字背景
              const textWidth = ctx.measureText(label).width;
              const padding = 4;
              ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
              ctx.fillRect(
                (node.x || 0) - textWidth / 2 - padding,
                (node.y || 0) - fontSize / 2 - padding,
                textWidth + padding * 2,
                fontSize + padding * 2
              );

              // 绘制文字
              ctx.fillStyle = getNodeColor(node);
              ctx.fillText(label, node.x || 0, node.y || 0);

              // 高亮悬停的节点
              if (hoveredNode && hoveredNode.id === node.id) {
                ctx.strokeStyle = getNodeColor(node);
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(node.x || 0, node.y || 0, getNodeSize(node) + 3, 0, 2 * Math.PI);
                ctx.stroke();
              }
            }}
            width={isFullscreen ? window.innerWidth : undefined}
            height={isFullscreen ? window.innerHeight - 120 : height}
            cooldownTicks={100}
          />
        )}

        {/* 节点详情弹窗 */}
        {showNodeDetail && selectedNode && (
          <div className="absolute top-4 right-4 bg-white rounded-lg border border-gray-200 shadow-lg p-4 max-w-sm z-10">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">节点详情</h3>
              <button
                onClick={() => {
                  setShowNodeDetail(false);
                  setSelectedNode(null);
                  setHighlightedPath(new Set());
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-gray-700">名称：</span>
                <span className="text-gray-900">{selectedNode.name}</span>
              </div>
              {selectedNode.type && (
                <div>
                  <span className="font-medium text-gray-700">类型：</span>
                  <span className="text-gray-900">{selectedNode.type}</span>
                </div>
              )}
              {selectedNode.metadata?.description && (
                <div>
                  <span className="font-medium text-gray-700">描述：</span>
                  <span className="text-gray-900">{selectedNode.metadata.description}</span>
                </div>
              )}
              <div>
                <span className="font-medium text-gray-700">连接数：</span>
                <span className="text-gray-900">
                  {
                    graphData.links.filter(
                      (l) => l.source === selectedNode.id || l.target === selectedNode.id
                    ).length
                  }
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
