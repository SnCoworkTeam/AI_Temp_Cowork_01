'use client';

import React, { useCallback, useMemo, useEffect } from 'react';
import { WorkflowProgress } from '../AgentWorkflowInterface';

// 检查是否安装了reactflow
let ReactFlow: any = null;
let Background: any = null;
let Controls: any = null;
let MiniMap: any = null;
let useNodesState: any = null;
let useEdgesState: any = null;
let ConnectionLineType: any = null;

try {
  const reactflow = require('reactflow');
  ReactFlow = reactflow.default || reactflow.ReactFlow;
  Background = reactflow.Background;
  Controls = reactflow.Controls;
  MiniMap = reactflow.MiniMap;
  useNodesState = reactflow.useNodesState;
  useEdgesState = reactflow.useEdgesState;
  ConnectionLineType = reactflow.ConnectionLineType;
} catch (e) {
  console.warn('reactflow not installed, using fallback visualization');
}

/**
 * WorkflowVisualizer组件属性
 */
export interface WorkflowVisualizerProps {
  /** 工作流进度 */
  progress: WorkflowProgress;
  /** 是否加载中 */
  isLoading?: boolean;
  /** 节点点击回调 */
  onNodeClick?: (nodeId: string) => void;
}

/**
 * 自定义工作流节点组件
 */
const WorkflowNode = ({ data }: { data: any }) => {
  const getNodeStyle = (type: string, isActive: boolean, status?: string) => {
    const baseStyle: React.CSSProperties = {
      padding: '10px',
      borderRadius: '8px',
      border: '2px solid',
      minWidth: '120px',
      textAlign: 'center',
      transition: 'all 0.3s ease',
    };

    const typeStyles: Record<string, React.CSSProperties> = {
      start: {
        borderColor: '#10B981',
        backgroundColor: isActive ? '#D1FAE5' : '#ECFDF5',
        color: '#065F46',
      },
      end: {
        borderColor: '#EF4444',
        backgroundColor: isActive ? '#FEE2E2' : '#FEF2F2',
        color: '#991B1B',
      },
      task: {
        borderColor: '#3B82F6',
        backgroundColor: isActive ? '#DBEAFE' : '#EFF6FF',
        color: '#1E40AF',
      },
      condition: {
        borderColor: '#F59E0B',
        backgroundColor: isActive ? '#FEF3C7' : '#FFFBEB',
        color: '#92400E',
      },
      agent: {
        borderColor: '#8B5CF6',
        backgroundColor: isActive ? '#E9D5FF' : '#F3E8FF',
        color: '#6B21A8',
      },
    };

    const style = { ...baseStyle, ...(typeStyles[type] || typeStyles.task) };

    if (status === 'completed') {
      style.borderColor = '#10B981';
      style.backgroundColor = '#D1FAE5';
    } else if (status === 'failed') {
      style.borderColor = '#EF4444';
      style.backgroundColor = '#FEE2E2';
    }

    return style;
  };

  return (
    <div style={getNodeStyle(data.type || 'task', data.isActive, data.status)}>
      <div style={{ fontWeight: 600, fontSize: '14px' }}>{data.label || data.id}</div>
      {data.description && (
        <div style={{ fontSize: '11px', color: '#6B7280', marginTop: '4px' }}>
          {data.description}
        </div>
      )}
      {data.status && (
        <div
          style={{
            fontSize: '11px',
            marginTop: '4px',
            color:
              data.status === 'completed'
                ? '#059669'
                : data.status === 'failed'
                  ? '#DC2626'
                  : '#2563EB',
          }}
        >
          {data.status === 'completed'
            ? '✓ 完成'
            : data.status === 'failed'
              ? '✗ 失败'
              : data.status === 'running'
                ? '⟳ 运行中'
                : '○ 等待中'}
        </div>
      )}
      {data.progress !== undefined && data.status === 'running' && (
        <div
          style={{
            marginTop: '6px',
            height: '4px',
            backgroundColor: '#E5E7EB',
            borderRadius: '2px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${data.progress}%`,
              backgroundColor: '#3B82F6',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      )}
    </div>
  );
};

/**
 * 工作流可视化组件
 *
 * 显示工作流的执行进度和节点状态
 * 如果安装了reactflow，使用图形化展示；否则使用列表展示
 */
export const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  progress,
  isLoading = false,
  onNodeClick,
}) => {
  const {
    name,
    status,
    progress: progressPercent = 0,
    currentNodeName,
    currentNodeId,
    nodeStatuses = {},
    startTime,
    endTime,
    error,
  } = progress;

  // 如果安装了reactflow，使用图形化展示
  if (ReactFlow && useNodesState && useEdgesState) {
    return (
      <GraphicalWorkflowVisualizer
        progress={progress}
        isLoading={isLoading}
        onNodeClick={onNodeClick}
      />
    );
  }

  // 否则使用列表展示（原有实现）
  return (
    <ListWorkflowVisualizer progress={progress} isLoading={isLoading} onNodeClick={onNodeClick} />
  );
};

/**
 * 图形化工作流可视化组件（使用React Flow）
 */
const GraphicalWorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  progress,
  isLoading,
  onNodeClick,
}) => {
  const { nodeStatuses = {}, currentNodeId } = progress;

  // 转换节点数据为React Flow格式
  const reactFlowNodes = useMemo(() => {
    const nodes = Object.entries(nodeStatuses).map(
      ([nodeId, nodeStatus]: [string, any], index) => ({
        id: nodeId,
        type: 'workflowNode',
        position: {
          x: (index % 4) * 200,
          y: Math.floor(index / 4) * 150,
        },
        data: {
          id: nodeId,
          label: nodeId,
          type: 'task',
          isActive: nodeId === currentNodeId,
          status: nodeStatus.status,
          progress: nodeStatus.progress,
          description: nodeStatus.description,
        },
      })
    );

    return nodes;
  }, [nodeStatuses, currentNodeId]);

  // 创建边（简单的链式连接）
  const reactFlowEdges = useMemo(() => {
    const nodes = Object.keys(nodeStatuses);
    const edges = [];

    for (let i = 0; i < nodes.length - 1; i++) {
      edges.push({
        id: `edge-${nodes[i]}-${nodes[i + 1]}`,
        source: nodes[i],
        target: nodes[i + 1],
        type: ConnectionLineType?.SmoothStep || 'smoothstep',
        animated: nodes[i] === currentNodeId,
        style: {
          stroke: nodes[i] === currentNodeId ? '#3B82F6' : '#9CA3AF',
          strokeWidth: nodes[i] === currentNodeId ? 3 : 2,
        },
      });
    }

    return edges;
  }, [nodeStatuses, currentNodeId]);

  const [rfNodes, setRfNodes, onNodesChange] = useNodesState(reactFlowNodes);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(reactFlowEdges);

  // 当props变化时更新节点和边
  useEffect(() => {
    setRfNodes(reactFlowNodes);
  }, [reactFlowNodes, setRfNodes]);

  useEffect(() => {
    setRfEdges(reactFlowEdges);
  }, [reactFlowEdges, setRfEdges]);

  const onNodeClickHandler = useCallback(
    (event: React.MouseEvent, node: any) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  const nodeTypes = useMemo(
    () => ({
      workflowNode: WorkflowNode,
    }),
    []
  );

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '400px' }}>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickHandler}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        {Background && <Background />}
        {Controls && <Controls />}
        {MiniMap && <MiniMap />}
      </ReactFlow>
    </div>
  );
};

/**
 * 列表工作流可视化组件（原有实现，作为fallback）
 */
const ListWorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  progress,
  isLoading,
  onNodeClick,
}) => {
  const {
    name,
    status,
    progress: progressPercent = 0,
    currentNodeName,
    nodeStatuses = {},
    startTime,
    endTime,
    error,
  } = progress;

  // 状态颜色映射
  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    running: 'bg-blue-100 text-blue-800 border-blue-300',
    completed: 'bg-green-100 text-green-800 border-green-300',
    failed: 'bg-red-100 text-red-800 border-red-300',
    paused: 'bg-gray-100 text-gray-800 border-gray-300',
    cancelled: 'bg-gray-100 text-gray-800 border-gray-300',
  };

  // 状态文本映射
  const statusText = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停',
    cancelled: '已取消',
  };

  // 计算执行时间
  const executionTime =
    startTime && endTime
      ? ((endTime - startTime) / 1000).toFixed(2)
      : startTime
        ? ((Date.now() - startTime) / 1000).toFixed(2)
        : null;

  return (
    <div className="h-full flex flex-col bg-white border-b border-gray-200">
      {/* 工作流头部信息 */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-gray-900">{name || '工作流执行'}</h3>
            {status && (
              <span
                className={`px-2.5 py-1 text-xs font-medium rounded-full border ${statusColors[status] || statusColors.pending}`}
              >
                {statusText[status] || status}
              </span>
            )}
          </div>
          {executionTime && (
            <div className="text-sm text-gray-500">执行时间: {executionTime}秒</div>
          )}
        </div>
      </div>

      {/* 进度条 */}
      {status === 'running' && (
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">执行进度</span>
            <span className="text-sm text-gray-600">{progressPercent}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          {currentNodeName && (
            <div className="mt-2 text-xs text-gray-600">
              当前节点: <span className="font-medium">{currentNodeName}</span>
            </div>
          )}
        </div>
      )}

      {/* 节点状态列表 */}
      {Object.keys(nodeStatuses).length > 0 && (
        <div className="flex-1 overflow-y-auto px-4 py-3">
          <h4 className="text-sm font-medium text-gray-700 mb-3">节点状态</h4>
          <div className="space-y-2">
            {Object.entries(nodeStatuses).map(([nodeId, nodeStatus]: [string, any]) => {
              const nodeStatusColors: Record<string, string> = {
                pending: 'bg-yellow-50 border-yellow-200',
                running: 'bg-blue-50 border-blue-200',
                completed: 'bg-green-50 border-green-200',
                failed: 'bg-red-50 border-red-200',
                skipped: 'bg-gray-50 border-gray-200',
              };

              const nodeStatusText: Record<string, string> = {
                pending: '等待中',
                running: '运行中',
                completed: '已完成',
                failed: '失败',
                skipped: '已跳过',
              };

              const status = String(nodeStatus?.status || 'pending');

              return (
                <div
                  key={nodeId}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    nodeStatusColors[status] || nodeStatusColors.pending
                  } ${onNodeClick ? 'hover:shadow-md' : ''}`}
                  onClick={() => onNodeClick?.(nodeId)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">{nodeId}</span>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded ${
                          status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : status === 'running'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {nodeStatusText[status] || status}
                      </span>
                    </div>
                    {nodeStatus.progress !== undefined && (
                      <span className="text-xs text-gray-500">{nodeStatus.progress}%</span>
                    )}
                  </div>
                  {nodeStatus.error && (
                    <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                      {nodeStatus.error}
                    </div>
                  )}
                  {nodeStatus.progress !== undefined && nodeStatus.status === 'running' && (
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${nodeStatus.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 错误信息 */}
      {error && (
        <div className="px-4 py-3 bg-red-50 border-t border-red-200">
          <div className="flex items-start gap-2">
            <svg
              className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">执行错误</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* 加载指示器 */}
      {isLoading && (
        <div className="px-4 py-3 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center gap-2 text-sm text-blue-700">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>正在处理...</span>
          </div>
        </div>
      )}

      {/* 空状态 */}
      {!status && Object.keys(nodeStatuses).length === 0 && !error && (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <p className="mt-2 text-sm">暂无工作流执行信息</p>
            <p className="mt-1 text-xs text-gray-400">安装 reactflow 以获得更好的可视化体验</p>
          </div>
        </div>
      )}
    </div>
  );
};
