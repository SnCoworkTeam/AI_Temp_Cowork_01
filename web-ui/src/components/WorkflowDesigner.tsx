'use client';

import React, { useCallback, useMemo, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  useNodesState,
  useEdgesState,
  NodeTypes,
  EdgeTypes,
  MarkerType,
  Position,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { NodePanel } from './NodePanel';
import { PropertyPanel } from './PropertyPanel';
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
import { WorkflowConfig, WorkflowConnection } from '@/types/workflow';
import { saveWorkflow, getWorkflow } from '@/lib/api/workflow';
import { fetchLLMDefaultConfig, getDefaultLLMModel } from '@/lib/config/llm';

// 将 nodeTypes 定义在组件外部，避免每次渲染时重新创建
// 使用 Object.freeze 确保对象不会被修改
const nodeTypes: NodeTypes = Object.freeze({
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
}) as NodeTypes;

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

// 自动调整视图的组件
function AutoFitView({ nodes, loading }: { nodes: Node[]; loading: boolean }) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (!loading && nodes.length > 0) {
      // 延迟调整视图，确保节点已渲染
      const timer = setTimeout(() => {
        fitView({ padding: 0.2, duration: 300 });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [nodes.length, loading, fitView]);

  return null;
}

interface WorkflowDesignerProps {
  workflowId?: string;
  onSave?: (workflowId: string) => void;
}

export function WorkflowDesigner({ workflowId, onSave }: WorkflowDesignerProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  // 生成唯一的工作流名称
  const generateUniqueWorkflowName = () => {
    const timestamp = Date.now();
    return `新工作流_${timestamp}`;
  };

  const [workflowName, setWorkflowName] = useState(generateUniqueWorkflowName());
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // 加载LLM默认配置
  React.useEffect(() => {
    loadLLMDefaultConfig().catch(console.error);
  }, []);

  // 加载工作流
  React.useEffect(() => {
    if (workflowId) {
      console.log('[WorkflowDesigner] useEffect triggered, workflowId:', workflowId);
      loadWorkflow(workflowId);
    } else {
      console.log('[WorkflowDesigner] No workflowId provided, starting with empty workflow');
    }
  }, [workflowId]);

  const loadWorkflow = async (id: string) => {
    try {
      setLoading(true);
      console.log('[WorkflowDesigner] Loading workflow:', id);
      console.log('[WorkflowDesigner] Calling getWorkflow API...');

      const workflow = await getWorkflow(id);
      console.log('[WorkflowDesigner] Workflow data received:', workflow);
      console.log('[WorkflowDesigner] Workflow keys:', Object.keys(workflow || {}));

      if (!workflow) {
        console.error('[WorkflowDesigner] No workflow data returned from API');
        alert('工作流数据为空，请检查工作流ID是否正确');
        return;
      }

      if (workflow?.workflow) {
        console.log('[WorkflowDesigner] Found workflow object');
        console.log('[WorkflowDesigner] Workflow name:', workflow.workflow.name);
        console.log('[WorkflowDesigner] Nodes count:', workflow.workflow.nodes?.length || 0);
        console.log(
          '[WorkflowDesigner] Connections count:',
          workflow.workflow.connections?.length || 0
        );

        setWorkflowName(workflow.workflow.name || '未命名工作流');
        setWorkflowDescription(workflow.workflow.description || '');

        // 转换节点
        const nodesArray = workflow.workflow.nodes || [];
        console.log('[WorkflowDesigner] Raw nodes array:', nodesArray);

        if (nodesArray.length === 0) {
          console.warn('[WorkflowDesigner] No nodes found in workflow');
          setNodes([]);
        } else {
          const flowNodes: Node[] = nodesArray.map((node: any, index: number) => {
            console.log(`[WorkflowDesigner] Processing node ${index}:`, node);

            // 处理 node_type：可能是字符串或对象
            let nodeType = 'task';
            if (typeof node.node_type === 'string') {
              nodeType = node.node_type;
            } else if (node.node_type?.value) {
              nodeType = node.node_type.value;
            } else if (node.type) {
              nodeType = node.type;
            }

            // 处理 position：可能是对象 {x, y} 或 null
            let position = { x: 0, y: 0 };
            if (node.position) {
              if (
                typeof node.position === 'object' &&
                'x' in node.position &&
                'y' in node.position
              ) {
                position = {
                  x: typeof node.position.x === 'number' ? node.position.x : 0,
                  y: typeof node.position.y === 'number' ? node.position.y : 0,
                };
              }
            } else {
              // 如果没有位置信息，使用简单的网格布局（与预览页面保持一致）
              position = {
                x: (index % 4) * 250,
                y: Math.floor(index / 4) * 150,
              };
            }

            const flowNode = {
              id: node.id || `node-${index}`,
              type: nodeType,
              position: position,
              data: {
                label: node.name || node.id || `节点 ${index + 1}`,
                name: node.name || node.id || `节点 ${index + 1}`, // 确保 name 字段存在
                config: node.config || {},
                ...node,
              },
            };

            console.log(`[WorkflowDesigner] Converted node ${index}:`, flowNode);
            return flowNode;
          });

          console.log('[WorkflowDesigner] Converted nodes:', flowNodes);
          setNodes(flowNodes);
        }

        // 转换边
        const connectionsArray = workflow.workflow.connections || [];
        console.log('[WorkflowDesigner] Raw connections array:', connectionsArray);

        if (connectionsArray.length === 0) {
          console.warn('[WorkflowDesigner] No connections found in workflow');
          setEdges([]);
        } else {
          const flowEdges: Edge[] = connectionsArray
            .map((conn: any, index: number) => {
              console.log(`[WorkflowDesigner] Processing connection ${index}:`, conn);

              // 处理 source 和 target：可能是对象 {node_id} 或字符串
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
                console.warn(
                  `[WorkflowDesigner] Invalid connection ${index}: source=${sourceId}, target=${targetId}`
                );
              }

              const flowEdge = {
                id: conn.id || `edge-${sourceId}-${targetId}-${index}`,
                source: sourceId,
                target: targetId,
                type: 'smoothstep',
                animated: false,
                label: conn.label || '',
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                },
              };

              console.log(`[WorkflowDesigner] Converted edge ${index}:`, flowEdge);
              return flowEdge;
            })
            .filter((edge: Edge) => edge.source && edge.target); // 过滤掉无效的连接

          console.log('[WorkflowDesigner] Converted edges:', flowEdges);
          setEdges(flowEdges);
        }

        console.log('[WorkflowDesigner] Workflow loaded successfully');
        console.log('[WorkflowDesigner] Setting nodes and edges...');
      } else {
        console.error('[WorkflowDesigner] No workflow.workflow found in response');
        console.error(
          '[WorkflowDesigner] Response structure:',
          JSON.stringify(workflow, null, 2).substring(0, 1000)
        );
        setSaveMessage({ type: 'error', text: '工作流数据格式不正确' });
        setTimeout(() => setSaveMessage(null), 5000);
      }
    } catch (error: any) {
      console.error('[WorkflowDesigner] Failed to load workflow:', error);
      console.error('[WorkflowDesigner] Error details:', {
        message: error?.message,
        stack: error?.stack,
        response: error?.response,
      });
      setSaveMessage({ type: 'error', text: `加载失败: ${error?.message || '未知错误'}` });
      setTimeout(() => setSaveMessage(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  // 添加节点
  const onAddNode = useCallback(
    (nodeType: string, position: { x: number; y: number }) => {
      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: nodeType,
        position,
        data: {
          label: getNodeLabel(nodeType),
          config: getDefaultConfig(nodeType),
          name: getNodeLabel(nodeType),
          type: nodeType,
        },
      };

      setNodes((nds) => {
        const updated = [...nds, newNode];
        return updated;
      });
      setSelectedNode(newNode);
    },
    [setNodes]
  );

  // 处理拖放事件
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const nodeType = event.dataTransfer.getData('application/reactflow');
      if (!nodeType) {
        return;
      }

      // 获取画布位置
      const reactFlowBounds = (event.currentTarget as HTMLElement).getBoundingClientRect();
      const position = {
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      };

      // 添加节点
      onAddNode(nodeType, position);
    },
    [onAddNode]
  );

  // 连接节点
  const onConnect = useCallback(
    (params: Connection) => {
      if (!params.source || !params.target) {
        return;
      }
      const newEdge: Edge = {
        id: `edge-${Date.now()}`,
        source: params.source,
        target: params.target,
        sourceHandle: params.sourceHandle || undefined,
        targetHandle: params.targetHandle || undefined,
        type: 'smoothstep',
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  // 节点选择
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  // 删除节点
  const onDeleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
      if (selectedNode?.id === nodeId) {
        setSelectedNode(null);
      }
    },
    [setNodes, setEdges, selectedNode]
  );

  // 更新节点配置
  const onUpdateNodeConfig = useCallback(
    (nodeId: string, config: Record<string, any>) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            return {
              ...node,
              data: {
                ...node.data,
                config,
                ...config,
              },
            };
          }
          return node;
        })
      );

      if (selectedNode?.id === nodeId) {
        setSelectedNode((nd) => {
          if (!nd) return null;
          return {
            ...nd,
            data: {
              ...nd.data,
              config,
              ...config,
            },
          };
        });
      }
    },
    [setNodes, selectedNode]
  );

  // 保存工作流
  const handleSave = async () => {
    if (nodes.length === 0) {
      alert('请至少添加一个节点');
      return;
    }

    setSaving(true);
    try {
      // 找到起始节点
      const startNode = nodes.find((n) => n.type === 'start') || nodes[0];
      if (!startNode) {
        alert('请添加一个起始节点');
        return;
      }

      // 构建工作流配置
      // 确保所有节点都有必需的字段
      const workflowNodes = nodes.map((node) => {
        const nodeType = node.type || 'task';
        return {
          id: node.id,
          name: node.data.label || node.data.name || node.id,
          node_type: nodeType, // 后端必需字段
          type: nodeType, // 前端使用的字段
          config: node.data.config || {},
          position: node.position || { x: 0, y: 0 },
          size: { width: 200, height: 100 },
          style: {},
          label: node.data.label,
          inputs: [], // 添加默认字段
          outputs: [], // 添加默认字段
          next_nodes: [], // 添加默认字段
        };
      });

      // 构建连接线，确保所有必需字段存在
      const workflowConnections: WorkflowConnection[] = edges
        .filter((edge) => edge.source && edge.target)
        .map((edge) => ({
          id: edge.id || `conn-${edge.source}-${edge.target}`,
          source: {
            node_id: edge.source as string,
            port: (edge.sourceHandle || 'output') as string,
          },
          target: {
            node_id: edge.target as string,
            port: (edge.targetHandle || 'input') as string,
          },
          label: (edge.label ? String(edge.label) : undefined) as string | undefined,
          condition: undefined,
          style: {},
          metadata: {},
        }));

      const workflowConfig: WorkflowConfig = {
        name: workflowName.trim() || '未命名工作流',
        description: workflowDescription || '',
        version: '1.0.0',
        nodes: workflowNodes,
        connections: workflowConnections,
        start_node_id: startNode.id,
        end_node_ids: nodes.filter((n) => n.type === 'end').map((n) => n.id),
        variables: {},
        metadata: {},
      };

      const result = await saveWorkflow(workflowConfig);
      setSaveMessage({ type: 'success', text: '工作流保存成功！' });
      setTimeout(() => {
        if (onSave) {
          onSave(result.workflow_id);
        }
        // 保存成功后，跳转到工作流列表页面
        if (typeof window !== 'undefined') {
          window.location.href = '/workflows';
        }
      }, 1500);
    } catch (error: any) {
      console.error('[WorkflowDesigner] Failed to save workflow:', error);

      // 检查是否是404错误（端点不存在）
      const is404 =
        error?.statusCode === 404 ||
        error?.status === 404 ||
        (error?.message && error.message.includes('404'));

      let errorMessage = error?.details || error?.message || '保存工作流失败';

      // 如果是404错误，提供更友好的提示
      if (is404) {
        errorMessage = '工作流保存功能暂未实现（API端点不存在）';
      }

      setSaveMessage({ type: 'error', text: `保存失败: ${errorMessage}` });
      setTimeout(() => setSaveMessage(null), 5000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* 加载遮罩 */}
      {loading && (
        <div className="absolute inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 shadow-xl">
            <div className="flex items-center gap-4">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-200 border-t-blue-600"></div>
              <div>
                <p className="font-medium text-gray-900">正在加载工作流...</p>
                <p className="text-sm text-gray-500 mt-1">请稍候</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 消息提示 */}
      {saveMessage && (
        <div
          className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 animate-in slide-in-from-top-5 ${
            saveMessage.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}
        >
          <div
            className={`flex-shrink-0 ${saveMessage.type === 'success' ? 'text-green-600' : 'text-red-600'}`}
          >
            {saveMessage.type === 'success' ? (
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            ) : (
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            )}
          </div>
          <p className="font-medium">{saveMessage.text}</p>
          <button
            onClick={() => setSaveMessage(null)}
            className="ml-4 text-gray-400 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      )}

      {/* 节点面板 */}
      <NodePanel onAddNode={onAddNode} />

      {/* 主画布 */}
      <div className="flex-1 relative">
        <div className="absolute top-0 left-0 right-0 bg-white border-b shadow-sm p-4 z-10">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1">
              <div className="flex-shrink-0">
                <label className="text-xs text-gray-500 mb-1 block">工作流名称</label>
                <input
                  type="text"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="输入工作流名称"
                />
              </div>
              <div className="flex-1">
                <label className="text-xs text-gray-500 mb-1 block">描述</label>
                <input
                  type="text"
                  value={workflowDescription}
                  onChange={(e) => setWorkflowDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="输入工作流描述（可选）"
                />
              </div>
            </div>
            <div className="flex-shrink-0">
              <button
                onClick={handleSave}
                disabled={saving || loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm hover:shadow-md transition-all flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    <span>保存中...</span>
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span>保存工作流</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="h-full pt-16" onDragOver={onDragOver} onDrop={onDrop}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={useMemo(() => nodeTypes, [])}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            className="bg-gray-50"
            proOptions={{ hideAttribution: true }}
          >
            <Background />
            <Controls />
            <MiniMap />
            <AutoFitView nodes={nodes} loading={loading} />
          </ReactFlow>
        </div>
      </div>

      {/* 属性面板 */}
      <PropertyPanel
        node={selectedNode}
        onUpdateNodeConfig={onUpdateNodeConfig}
        onDeleteNode={onDeleteNode}
      />
    </div>
  );
}

// 辅助函数
function getNodeLabel(nodeType: string): string {
  const labels: Record<string, string> = {
    start: '开始',
    end: '结束',
    llm: 'LLM节点',
    tool: '工具调用',
    condition: '条件判断',
    transform: '数据转换',
    http: 'HTTP请求',
    delay: '延迟',
    log: '日志',
  };
  return labels[nodeType] || nodeType;
}

// 缓存默认配置（避免重复请求）
let cachedLLMDefaultConfig: Record<string, any> | null = null;

async function loadLLMDefaultConfig(): Promise<Record<string, any>> {
  if (cachedLLMDefaultConfig) {
    return cachedLLMDefaultConfig;
  }
  try {
    const config = await fetchLLMDefaultConfig();
    cachedLLMDefaultConfig = config;
    return config;
  } catch (error) {
    console.warn('Failed to load LLM default config:', error);
    return {
      model: getDefaultLLMModel(),
      temperature: 0.7,
      prompt_template: '{input}',
    };
  }
}

function getDefaultConfig(nodeType: string): Record<string, any> {
  const defaults: Record<string, Record<string, any>> = {
    llm: {
      // 使用缓存的配置或默认值
      model: cachedLLMDefaultConfig?.model || getDefaultLLMModel(),
      temperature: cachedLLMDefaultConfig?.temperature || 0.7,
      prompt_template: cachedLLMDefaultConfig?.prompt_template || '{input}',
    },
    tool: {
      tool_name: '',
      parameters: {},
    },
    condition: {
      condition: 'True',
    },
    transform: {
      transform: 'identity',
      mapping: {},
    },
    http: {
      url: '',
      method: 'GET',
      headers: {},
      body: {},
    },
  };
  return defaults[nodeType] || {};
}
