'use client';

import React, { useRef, useCallback, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// 动态导入以避免SSR问题，使用forwardRef支持
const ForceGraph2D = dynamic(() => import('react-force-graph').then((mod) => mod.ForceGraph2D), {
  ssr: false,
});

interface GraphVisualizationProps {
  data: { nodes: any[]; links: any[] };
  onNodeClick?: (node: any) => void;
  onNodeHover?: (node: any) => void;
  loading?: boolean;
  width?: number;
  height?: number;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = React.memo(
  ({ data, onNodeClick, onNodeHover, loading = false, width = 800, height = 600 }) => {
    const graphContainerRef = useRef<HTMLDivElement>(null);
    const [mounted, setMounted] = useState(false);
    const [hoveredNode, setHoveredNode] = useState<any>(null);

    useEffect(() => {
      setMounted(true);
    }, []);

    const handleNodeClick = useCallback(
      (node: any) => {
        if (onNodeClick) {
          onNodeClick(node);
        }
      },
      [onNodeClick]
    );

    const handleNodeHover = useCallback(
      (node: any) => {
        setHoveredNode(node);
        if (onNodeHover) {
          onNodeHover(node);
        }
      },
      [onNodeHover]
    );

    // 节点类型颜色映射（更美观的配色）
    const getNodeColor = (node: any) => {
      const type = node.group || node.type;
      const colorMap: { [key: string]: string } = {
        sap_module: '#1890ff', // 蓝色 - SAP模块
        sap_sub_module: '#52c41a', // 绿色 - SAP子模块
        concept: '#fa8c16', // 橙色 - 概念
        entity: '#722ed1', // 紫色 - 实体
        agent: '#eb2f96', // 粉色 - 智能体
        document: '#13c2c2', // 青色 - 文档
        knowledge_base: '#f5222d', // 红色 - 知识库
        default: '#8c8c8c', // 灰色 - 默认
      };
      return colorMap[type] || colorMap['default'];
    };

    // 节点大小计算
    const getNodeSize = (node: any) => {
      const baseSize = 8;
      const connections = (data.links || []).filter(
        (link: any) => link.source === node.id || link.target === node.id
      ).length;
      return baseSize + Math.min(connections * 2, 12);
    };

    if (!mounted || loading) {
      return (
        <div
          style={{
            width: '100%',
            height,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '8px',
            color: 'white',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '18px', marginBottom: '8px' }}>加载中...</div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>正在加载知识图谱数据</div>
          </div>
        </div>
      );
    }

    if (!data || !data.nodes || data.nodes.length === 0) {
      return (
        <div
          style={{
            width: '100%',
            height,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f5f5f5',
            borderRadius: '8px',
            border: '2px dashed #d9d9d9',
          }}
        >
          <div style={{ textAlign: 'center', color: '#8c8c8c' }}>
            <div style={{ fontSize: '18px', marginBottom: '8px' }}>暂无数据</div>
            <div style={{ fontSize: '14px' }}>知识图谱中还没有节点数据</div>
          </div>
        </div>
      );
    }

    return (
      <div
        ref={graphContainerRef}
        style={{
          width: '100%',
          height,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {ForceGraph2D && mounted && (
          <ForceGraph2D
            graphData={data}
            nodeLabel={(node: any) => {
              const name = node.name || node.id || '节点';
              const type = node.type_cn || node.type || '';
              return `${name}${type ? ` (${type})` : ''}`;
            }}
            nodeColor={(node: any) => getNodeColor(node)}
            linkColor={(link: any) => {
              // 根据关系类型设置边的颜色
              const type = link.type || 'related';
              const colorMap: { [key: string]: string } = {
                part_of: 'rgba(24, 144, 255, 0.4)',
                related_to: 'rgba(82, 196, 26, 0.4)',
                contains: 'rgba(250, 140, 22, 0.4)',
                default: 'rgba(0, 0, 0, 0.2)',
              };
              return colorMap[type] || colorMap['default'];
            }}
            linkWidth={(link: any) => {
              // 根据关系类型设置边的宽度
              return link.type === 'part_of' ? 3 : 2;
            }}
            nodeVal={(node: any) => getNodeSize(node)}
            nodeRelSize={6}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.25}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            onNodeDragEnd={(node: any) => {
              node.fx = node.x;
              node.fy = node.y;
            }}
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = node.name || node.id || '节点';
              const fontSize = Math.max(12 / Math.sqrt(globalScale), 10);
              ctx.font = `bold ${fontSize}px "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';

              // 绘制文字背景（提高可读性）
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
            width={width || 800}
            height={height || 600}
            cooldownTicks={100}
            // 移除onEngineStop中的zoomToFit调用，因为dynamic导入的组件不支持ref
          />
        )}
      </div>
    );
  }
);
