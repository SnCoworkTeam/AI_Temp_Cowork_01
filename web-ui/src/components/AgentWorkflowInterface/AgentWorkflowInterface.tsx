'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  AgentResponsePayload,
  WorkflowProgressPayload,
  WorkflowExecutionState,
  AgentExecutionState,
  MessageType,
} from '@/types/agent-protocol';
import { WorkflowVisualizer } from './WorkflowVisualizer';
import { AgentChat } from './AgentChat';

/**
 * 智能体状态接口
 */
export interface AgentState {
  /** 智能体ID */
  agentId?: string;
  /** 智能体名称 */
  agentName?: string;
  /** 当前节点ID */
  nodeId?: string;
  /** 节点名称 */
  nodeName?: string;
  /** 状态 */
  status: 'idle' | 'thinking' | 'executing' | 'awaiting_input' | 'completed' | 'error';
  /** 当前消息内容 */
  currentMessage?: string;
  /** 建议的问题 */
  suggestions?: string[];
  /** 错误信息 */
  error?: string;
  /** 执行ID */
  executionId?: string;
}

/**
 * 工作流进度接口
 */
export interface WorkflowProgress {
  /** 工作流ID */
  id?: string;
  /** 执行ID */
  executionId?: string;
  /** 工作流名称 */
  name?: string;
  /** 执行状态 */
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  /** 进度百分比 (0-100) */
  progress?: number;
  /** 当前节点ID */
  currentNodeId?: string;
  /** 当前节点名称 */
  currentNodeName?: string;
  /** 节点状态映射 */
  nodeStatuses?: Record<
    string,
    {
      status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
      progress?: number;
      error?: string;
    }
  >;
  /** 开始时间 */
  startTime?: number;
  /** 结束时间 */
  endTime?: number;
  /** 错误信息 */
  error?: string;
}

/**
 * 智能体响应接口（扩展AgentResponsePayload）
 */
export interface AgentResponse extends AgentResponsePayload {
  /** 是否需要进一步输入 */
  requires_further_input?: boolean;
  /** 建议的问题 */
  suggested_questions?: string[];
  /** 下一个节点ID */
  next_node?: string;
  /** 工作流ID */
  workflow_id?: string;
}

/**
 * AgentWorkflowInterface组件属性
 */
export interface AgentWorkflowInterfaceProps {
  /** 工作流ID */
  workflowId?: string;
  /** 智能体ID */
  agentId?: string;
  /** 初始输入 */
  initialInput?: string;
  /** 是否自动开始 */
  autoStart?: boolean;
  /** 错误处理回调 */
  onError?: (error: Error) => void;
  /** 工作流完成回调 */
  onWorkflowComplete?: (result: any) => void;
}

/**
 * 智能体工作流界面组件
 *
 * 整合智能体聊天和工作流可视化的统一界面
 */
export const AgentWorkflowInterface: React.FC<AgentWorkflowInterfaceProps> = ({
  workflowId,
  agentId,
  initialInput,
  autoStart = false,
  onError,
  onWorkflowComplete,
}) => {
  const [currentAgent, setCurrentAgent] = useState<AgentState | null>(null);
  const [workflowProgress, setWorkflowProgress] = useState<WorkflowProgress>({
    status: 'pending',
    progress: 0,
    nodeStatuses: {},
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const errorToastRef = useRef<((message: string) => void) | null>(null);

  // WebSocket连接管理
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectAttemptRef = useRef(0);
  const maxReconnectAttempts = 5;

  /**
   * 显示错误提示
   */
  const showErrorToast = useCallback((message: string) => {
    setError(message);
    if (errorToastRef.current) {
      errorToastRef.current(message);
    }
    // 3秒后清除错误
    setTimeout(() => setError(null), 3000);
  }, []);

  /**
   * 推进工作流到下一个节点
   */
  const advanceWorkflow = useCallback(
    async (nextNodeId: string, workflowId?: string) => {
      try {
        setIsLoading(true);

        const targetWorkflowId = workflowId || workflowProgress.id;
        if (!targetWorkflowId) {
          throw new Error('工作流ID不存在');
        }

        // 调用API推进工作流
        const response = await fetch('/api/workflows/advance', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            workflow_id: targetWorkflowId,
            execution_id: workflowProgress.executionId,
            next_node_id: nextNodeId,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        // 更新工作流进度
        if (result.progress) {
          setWorkflowProgress((prev: WorkflowProgress) => ({
            ...prev,
            currentNodeId: nextNodeId,
            currentNodeName: result.currentNodeName || nextNodeId,
            progress: result.progress,
            status: result.status || 'running',
            nodeStatuses: {
              ...prev.nodeStatuses,
              [nextNodeId]: {
                status: 'running',
                progress: result.progress,
              },
            },
          }));
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('推进工作流失败');
        showErrorToast(error.message);
        if (onError) {
          onError(error);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [workflowProgress, showErrorToast, onError]
  );

  /**
   * 处理智能体响应
   */
  const handleAgentResponse = useCallback(
    (response: AgentResponse) => {
      try {
        // 更新智能体状态
        setCurrentAgent(
          (prev: AgentState | null) =>
            ({
              ...prev,
              agentId: response.agentId,
              agentName: response.agentName,
              status: response.requires_further_input ? 'awaiting_input' : 'executing',
              currentMessage: response.output?.content || '',
              suggestions: response.suggested_questions || [],
              executionId: response.executionId,
              error: response.error,
            }) as AgentState
        );

        // 如果需要进一步输入，等待用户输入
        if (response.requires_further_input) {
          setCurrentAgent(
            (prev: AgentState | null) =>
              ({
                ...prev,
                status: 'awaiting_input',
                suggestions: response.suggested_questions || [],
              }) as AgentState
          );
        } else if (response.next_node) {
          // 推进工作流执行
          advanceWorkflow(response.next_node, response.workflow_id);
        } else if (response.success) {
          // 执行完成
          setCurrentAgent(
            (prev: AgentState | null) =>
              ({
                ...prev,
                status: 'completed',
              }) as AgentState
          );

          if (onWorkflowComplete) {
            onWorkflowComplete(response.output);
          }
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('处理智能体响应失败');
        showErrorToast(error.message);
        setCurrentAgent(
          (prev: AgentState | null) =>
            ({
              ...prev,
              status: 'error',
              error: error.message,
            }) as AgentState
        );
        if (onError) {
          onError(error);
        }
      }
    },
    [onWorkflowComplete, onError, showErrorToast, advanceWorkflow]
  );

  /**
   * 处理WebSocket消息
   */
  const handleWebSocketMessage = useCallback(
    (message: any) => {
      try {
        switch (message.type) {
          case MessageType.WORKFLOW_PROGRESS:
            const progressData = message.payload as WorkflowProgressPayload;
            setWorkflowProgress((prev: WorkflowProgress) => ({
              ...prev,
              executionId: progressData.executionId,
              id: progressData.workflowId,
              name: progressData.workflowName,
              status: progressData.status as any,
              progress: progressData.progress,
              currentNodeId: progressData.currentNode,
              currentNodeName: progressData.currentNodeName,
              nodeStatuses: {
                ...prev.nodeStatuses,
                [progressData.currentNode]: {
                  status: 'running' as const,
                  progress: progressData.progress,
                },
              },
            }));
            break;

          case MessageType.WORKFLOW_NODE_COMPLETE:
            const nodeData = message.payload as any;
            setWorkflowProgress((prev: WorkflowProgress) => ({
              ...prev,
              nodeStatuses: {
                ...prev.nodeStatuses,
                [nodeData.nodeId]: {
                  status:
                    nodeData.status === 'success' ? ('completed' as const) : ('failed' as const),
                  error: nodeData.error,
                },
              },
            }));
            break;

          case MessageType.AGENT_RESPONSE:
            const agentData = message.payload as AgentResponsePayload;
            const agentResponse: AgentResponse = {
              ...agentData,
              requires_further_input: false,
              next_node: undefined,
              workflow_id: workflowProgress.id,
            };
            handleAgentResponse(agentResponse);
            break;

          case MessageType.WORKFLOW_COMPLETE:
            const completeData = message.payload as any;
            setWorkflowProgress((prev: WorkflowProgress) => ({
              ...prev,
              status: 'completed' as const,
              progress: 100,
              endTime: Date.now(),
            }));
            if (onWorkflowComplete) {
              onWorkflowComplete(completeData.result);
            }
            break;

          case MessageType.WORKFLOW_ERROR:
            const errorData = message.payload as any;
            setError(errorData.message || '工作流执行错误');
            setWorkflowProgress((prev: WorkflowProgress) => ({
              ...prev,
              status: 'failed' as const,
              error: errorData.message,
            }));
            if (onError) {
              onError(new Error(errorData.message));
            }
            break;

          case MessageType.AGENT_THINKING:
            setCurrentAgent(
              (prev: AgentState | null) =>
                ({
                  ...prev,
                  status: 'thinking' as const,
                }) as AgentState
            );
            break;

          default:
            console.warn('Unknown WebSocket message type:', message.type);
        }
      } catch (err) {
        console.error('Failed to handle WebSocket message:', err);
      }
    },
    [workflowProgress.id, handleAgentResponse, onWorkflowComplete, onError]
  );

  /**
   * 连接WebSocket
   */
  const connectWebSocket = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (!workflowId) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const gatewayUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || '';
      const baseUrl = gatewayUrl
        ? gatewayUrl.replace(/^http/, 'ws').replace(/\/+$/, '')
        : `${protocol}//${window.location.host}`;
      const wsUrl = `${baseUrl}/api/ws/workflows/${workflowId}`;

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttemptRef.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);

        // 自动重连逻辑
        if (reconnectAttemptRef.current < maxReconnectAttempts) {
          const delay = 1000 * Math.pow(2, reconnectAttemptRef.current);
          setTimeout(() => {
            reconnectAttemptRef.current += 1;
            connectWebSocket();
          }, delay);
        } else {
          showErrorToast('WebSocket连接失败，请刷新页面');
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        showErrorToast('WebSocket连接错误');
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      showErrorToast('无法建立WebSocket连接');
    }
  }, [workflowId, handleWebSocketMessage, showErrorToast]);

  /**
   * 发送WebSocket消息
   */
  const sendWebSocketMessage = useCallback(
    (message: any) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        const fullMessage = {
          ...message,
          timestamp: Date.now(),
          sessionId: workflowProgress.executionId || 'default',
          userId: 'current-user', // TODO: 从认证系统获取
        };
        ws.current.send(JSON.stringify(fullMessage));
        return true;
      }
      return false;
    },
    [workflowProgress.executionId]
  );

  /**
   * 处理用户输入
   */
  const handleUserInput = useCallback(
    async (input: string) => {
      if (!input.trim()) {
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // 更新智能体状态为执行中
        setCurrentAgent((prev) => ({
          ...prev,
          status: 'executing',
          currentMessage: undefined,
        }));

        // 优先使用WebSocket发送消息
        if (isConnected && sendWebSocketMessage) {
          const sent = sendWebSocketMessage({
            type: MessageType.CHAT_MESSAGE,
            payload: {
              content: input,
              workflow_id: workflowProgress.id || workflowId,
              execution_id: workflowProgress.executionId,
              current_node: currentAgent?.nodeId,
              agent_id: agentId || currentAgent?.agentId,
            },
          });

          if (sent) {
            // WebSocket发送成功，等待响应
            return;
          }
        }

        // 回退到HTTP API
        const response = await fetch('/api/agent/continue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            input,
            workflow_id: workflowProgress.id || workflowId,
            execution_id: workflowProgress.executionId,
            current_node: currentAgent?.nodeId,
            agent_id: agentId || currentAgent?.agentId,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result: AgentResponse = await response.json();

        // 处理智能体响应
        handleAgentResponse(result);

        // 如果响应中包含工作流进度信息，更新进度
        if (result.workflow_id) {
          setWorkflowProgress((prev) => ({
            ...prev,
            id: result.workflow_id,
            executionId: result.executionId || prev.executionId,
          }));
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('发送消息失败，请重试');
        showErrorToast(error.message);
        setCurrentAgent((prev) => ({
          ...prev,
          status: 'error',
          error: error.message,
        }));
        if (onError) {
          onError(error);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [
      currentAgent,
      workflowProgress,
      workflowId,
      agentId,
      handleAgentResponse,
      showErrorToast,
      onError,
      isConnected,
      sendWebSocketMessage,
    ]
  );

  /**
   * 初始化工作流
   */
  const initializeWorkflow = useCallback(async () => {
    if (!workflowId) {
      return;
    }

    try {
      setIsLoading(true);

      const response = await fetch(`/api/workflows/${workflowId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input: initialInput ? { content: initialInput } : {},
          agent_id: agentId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || '启动工作流失败');
      }

      const result = await response.json();

      setWorkflowProgress({
        id: workflowId,
        executionId: result.executionId,
        name: result.workflowName || workflowId,
        status: 'running',
        progress: 0,
        startTime: Date.now(),
      });

      // 如果有初始输入，发送给智能体
      if (initialInput) {
        await handleUserInput(initialInput);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('初始化工作流失败');
      showErrorToast(error.message);
      if (onError) {
        onError(error);
      }
    } finally {
      setIsLoading(false);
    }
  }, [workflowId, agentId, initialInput, handleUserInput, showErrorToast, onError]);

  // WebSocket连接管理
  useEffect(() => {
    if (workflowId) {
      connectWebSocket();
    }

    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [workflowId, connectWebSocket]);

  // 自动启动工作流
  useEffect(() => {
    if (autoStart && workflowId && !workflowProgress.id) {
      initializeWorkflow();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart, workflowId, workflowProgress.id]);

  // 初始化智能体状态
  useEffect(() => {
    if (agentId && !currentAgent) {
      setCurrentAgent({
        agentId,
        status: 'idle',
      });
    }
  }, [agentId, currentAgent]);

  // API端点验证（开发环境）
  useEffect(() => {
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      import('@/utils/api-validator')
        .then(({ validateApiEndpoints, logValidationResults }) => {
          validateApiEndpoints().then((results) => {
            const missingEndpoints = results.filter((r) => r.exists === false);
            if (missingEndpoints.length > 0) {
              console.warn(
                '以下API端点可能未实现:',
                missingEndpoints.map((e) => e.endpoint)
              );
              logValidationResults(results);
            }
          });
        })
        .catch(() => {
          // API验证工具未找到，忽略
        });
    }
  }, []);

  return (
    <div className="agent-workflow-interface flex flex-col h-full bg-gray-50">
      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium">{error}</p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setError(null)}
                className="inline-flex text-red-400 hover:text-red-600"
              >
                <span className="sr-only">关闭</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 工作流可视化器 */}
      <div className="flex-1 min-h-0">
        <WorkflowVisualizer progress={workflowProgress} isLoading={isLoading} />
      </div>

      {/* 智能体聊天界面 */}
      <div className="border-t border-gray-200">
        <AgentChat
          agent={currentAgent}
          onSendMessage={handleUserInput}
          isLoading={isLoading}
          suggestions={currentAgent?.suggestions}
        />
      </div>
    </div>
  );
};
