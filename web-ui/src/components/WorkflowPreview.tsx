'use client';

import React, { useMemo, useEffect, useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  Position,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  InformationCircleIcon,
  XMarkIcon,
  DocumentTextIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

import {
  LLMNode,
  ToolNode,
  ConditionNode,
  TransformNode,
  HTTPNode,
  StartNode,
  EndNode,
  LogNode,
  KnowledgeSearchNode,
  DocumentProcessingNode,
  KnowledgeEnhancementNode,
  AgentNode,
} from './nodes';
import { getWorkflow } from '@/lib/api/workflow';

// 节点类型映射（只读模式）
const nodeTypes = {
  llm: LLMNode,
  tool: ToolNode,
  condition: ConditionNode,
  transform: TransformNode,
  http: HTTPNode,
  start: StartNode,
  end: EndNode,
  log: LogNode,
  knowledge_search: KnowledgeSearchNode,
  document_processing: DocumentProcessingNode,
  knowledge_enhancement: KnowledgeEnhancementNode,
  agent: AgentNode,
};

interface WorkflowPreviewProps {
  workflowId: string;
  onClose?: () => void;
}

interface WorkflowStats {
  nodeCount: number;
  connectionCount: number;
  nodeTypes: Record<string, number>;
  startNodes: number;
  endNodes: number;
}

export function WorkflowPreview({ workflowId, onClose }: WorkflowPreviewProps) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workflowData, setWorkflowData] = useState<any>(null);
  const [stats, setStats] = useState<WorkflowStats | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showNodeDetails, setShowNodeDetails] = useState(false);
  const [showStats, setShowStats] = useState(true);
  // 注意：useReactFlow 需要在 ReactFlow 组件内部使用
  // 这里我们使用 ref 来访问 fitView

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  // 节点点击处理
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setShowNodeDetails(true);
  }, []);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      setError(null);

      const workflow = await getWorkflow(workflowId);

      if (!workflow?.workflow) {
        setError('工作流数据格式不正确');
        setLoading(false);
        return;
      }

      setWorkflowData(workflow.workflow);

      // 转换节点
      const nodesArray = workflow.workflow.nodes || [];
      const flowNodes: Node[] = nodesArray.map((node: any, index: number) => {
        let nodeType = 'task';
        if (typeof node.node_type === 'string') {
          nodeType = node.node_type;
        } else if (node.node_type?.value) {
          nodeType = node.node_type.value;
        } else if (node.type) {
          nodeType = node.type;
        }

        let position = { x: 0, y: 0 };
        if (node.position) {
          if (typeof node.position === 'object' && 'x' in node.position && 'y' in node.position) {
            position = {
              x: typeof node.position.x === 'number' ? node.position.x : 0,
              y: typeof node.position.y === 'number' ? node.position.y : 0,
            };
          }
        } else {
          // 如果没有位置信息，使用简单的网格布局
          position = {
            x: (index % 4) * 250,
            y: Math.floor(index / 4) * 150,
          };
        }

        return {
          id: node.id || `node-${index}`,
          type: nodeType,
          position,
          data: {
            label: node.name || node.id || `节点 ${index + 1}`,
            name: node.name || node.id || `节点 ${index + 1}`, // 确保 name 字段存在
            config: node.config || {},
            ...node, // 包含所有原始节点数据
          },
          // 只读模式：禁用选择和拖拽
          selectable: false,
          draggable: false,
        };
      });

      setNodes(flowNodes);

      // 转换边
      const connectionsArray = workflow.workflow.connections || [];
      const flowEdges: Edge[] = connectionsArray
        .map((conn: any, index: number) => {
          let sourceId = '';
          let targetId = '';

          if (typeof conn.source === 'string') {
            sourceId = conn.source;
          } else if (conn.source?.node_id) {
            sourceId = conn.source.node_id;
          }

          if (typeof conn.target === 'string') {
            targetId = conn.target;
          } else if (conn.target?.node_id) {
            targetId = conn.target.node_id;
          }

          if (!sourceId || !targetId) {
            return null;
          }

          return {
            id: conn.id || `edge-${sourceId}-${targetId}-${index}`,
            source: sourceId,
            target: targetId,
            type: 'smoothstep',
            animated: false,
            label: conn.label || conn.condition || '',
            markerEnd: {
              type: MarkerType.ArrowClosed,
            },
            // 只读模式：禁用选择和删除
            selectable: false,
            deletable: false,
          };
        })
        .filter((edge: Edge | null) => edge !== null) as Edge[];

      setEdges(flowEdges);

      // 计算统计信息
      const nodeTypeCounts: Record<string, number> = {};
      let startCount = 0;
      let endCount = 0;

      flowNodes.forEach((node) => {
        const type = node.type || 'unknown';
        nodeTypeCounts[type] = (nodeTypeCounts[type] || 0) + 1;
        if (type === 'start') startCount++;
        if (type === 'end') endCount++;
      });

      setStats({
        nodeCount: flowNodes.length,
        connectionCount: flowEdges.length,
        nodeTypes: nodeTypeCounts,
        startNodes: startCount,
        endNodes: endCount,
      });

      setLoading(false);
    } catch (err: any) {
      console.error('Failed to load workflow:', err);
      setError(err?.message || '加载工作流失败');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto mb-4"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <ChartBarIcon className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <p className="text-gray-600 font-medium mt-2">正在加载工作流...</p>
          <p className="text-gray-400 text-sm mt-1">请稍候</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-gray-50 rounded-lg">
        <div className="text-center max-w-md px-4">
          <div className="text-red-500 mb-4">
            <svg
              className="h-16 w-16 mx-auto"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => loadWorkflow()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg overflow-hidden shadow-sm">
      {/* 顶部工具栏 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-gray-900">
              {workflowData?.name || '工作流预览'}
            </h3>
            {workflowData?.version && (
              <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                v{workflowData.version}
              </span>
            )}
            {workflowData?.status && (
              <span
                className={`px-2 py-1 text-xs font-medium rounded-full ${
                  workflowData.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : workflowData.status === 'draft'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                }`}
              >
                {getStatusLabel(workflowData.status)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowStats(!showStats)}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
              title={showStats ? '隐藏统计' : '显示统计'}
            >
              <ChartBarIcon className="h-5 w-5" />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
                title="关闭"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>
        {workflowData?.description && (
          <p className="mt-2 text-sm text-gray-600">{workflowData.description}</p>
        )}
      </div>

      {/* 统计信息面板（可折叠） */}
      {showStats && stats && (
        <div className="bg-gray-50 border-b border-gray-200 p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-500 mb-1">节点数量</div>
                  <div className="text-2xl font-bold text-gray-900">{stats.nodeCount}</div>
                </div>
                <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <DocumentTextIcon className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-500 mb-1">连接数量</div>
                  <div className="text-2xl font-bold text-gray-900">{stats.connectionCount}</div>
                </div>
                <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg
                    className="h-6 w-6 text-green-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-500 mb-1">开始节点</div>
                  <div className="text-2xl font-bold text-gray-900">{stats.startNodes}</div>
                </div>
                <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg
                    className="h-6 w-6 text-purple-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14 5l7 7m0 0l-7 7m7-7H3"
                    />
                  </svg>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-500 mb-1">结束节点</div>
                  <div className="text-2xl font-bold text-gray-900">{stats.endNodes}</div>
                </div>
                <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
                  <svg
                    className="h-6 w-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* 节点类型统计 */}
          {Object.keys(stats.nodeTypes).length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="text-sm font-medium text-gray-700 mb-2">节点类型分布</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(stats.nodeTypes).map(([type, count]) => (
                  <span
                    key={type}
                    className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-800 border border-blue-200"
                  >
                    <span className="mr-1.5">{getNodeTypeLabel(type)}</span>
                    <span className="bg-blue-200 text-blue-900 px-1.5 py-0.5 rounded-full font-bold">
                      {count}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* React Flow 可视化 */}
      <div className="flex-1 relative" style={{ minHeight: '500px', height: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={true}
          panOnDrag={true}
          zoomOnScroll={true}
          zoomOnPinch={true}
          attributionPosition="bottom-left"
          style={{ width: '100%', height: '100%' }}
        >
          <Background />
          <Controls />
          <MiniMap
            nodeColor={(node: Node) => {
              const colors: Record<string, string> = {
                start: '#8b5cf6',
                end: '#ef4444',
                llm: '#3b82f6',
                tool: '#10b981',
                condition: '#f59e0b',
              };
              return colors[node.type || ''] || '#6b7280';
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
          />
        </ReactFlow>
      </div>

      {/* 节点详情侧边栏 */}
      {showNodeDetails && selectedNode && (
        <div className="absolute right-0 top-0 bottom-0 w-80 bg-white border-l border-gray-200 shadow-xl z-20 overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <h4 className="text-lg font-semibold text-gray-900">节点详情</h4>
            <button
              onClick={() => {
                setShowNodeDetails(false);
                setSelectedNode(null);
              }}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                节点名称
              </label>
              <p className="mt-1 text-sm font-semibold text-gray-900">
                {selectedNode.data.name || selectedNode.data.label || selectedNode.id}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                节点类型
              </label>
              <p className="mt-1 text-sm text-gray-900">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {selectedNode.data.name || getNodeTypeLabel(selectedNode.type || 'unknown')}
                </span>
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                节点ID
              </label>
              <p className="mt-1 text-sm text-gray-600 font-mono">{selectedNode.id}</p>
            </div>
            {selectedNode.data.config && Object.keys(selectedNode.data.config).length > 0 && (
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  配置信息
                </label>
                <pre className="mt-1 text-xs bg-gray-50 p-3 rounded-lg border border-gray-200 overflow-x-auto">
                  {JSON.stringify(selectedNode.data.config, null, 2)}
                </pre>
              </div>
            )}
            {selectedNode.position && (
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  位置
                </label>
                <p className="mt-1 text-sm text-gray-600">
                  X: {selectedNode.position.x.toFixed(0)}, Y: {selectedNode.position.y.toFixed(0)}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// 节点类型标签映射
function getNodeTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    start: '开始',
    end: '结束',
    llm: 'LLM',
    tool: '工具',
    condition: '条件',
    transform: '转换',
    http: 'HTTP',
    log: '日志',
    knowledge_search: '知识搜索',
    document_processing: '文档处理',
    knowledge_enhancement: '知识增强',
    agent: '智能体',
    task: '任务',
  };
  return labels[type] || type;
}

// 状态标签映射
function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿',
    active: '激活',
    inactive: '未激活',
    archived: '已归档',
  };
  return labels[status] || status;
}
