'use client';

import React, { useState, useEffect } from 'react';
import { getWorkflow, getExecutionStatus } from '@/lib/api/workflow';

interface WorkflowMessageProps {
  workflowId: string;
  workflowName?: string;
  executionId?: string;
  progress?: number;
  execution?: any;
  executing?: boolean;
  onUpdate?: (execution: any) => void;
}

interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

export const WorkflowMessage: React.FC<WorkflowMessageProps> = ({
  workflowId,
  workflowName,
  executionId,
  progress,
  execution,
  executing,
  onUpdate,
}) => {
  const [workflow, setWorkflow] = useState<any>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  useEffect(() => {
    if (execution) {
      updateStepsFromExecution(execution);
    }
  }, [execution]);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const data = await getWorkflow(workflowId);
      setWorkflow(data.workflow || data);

      if (data.workflow?.nodes) {
        const workflowSteps: WorkflowStep[] = data.workflow.nodes.map((node: any) => ({
          id: node.id,
          name: node.name,
          type: node.node_type || node.type,
          status: 'pending' as const,
        }));
        setSteps(workflowSteps);
      }
    } catch (error) {
      console.error('Failed to load workflow:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStepsFromExecution = (exec: any) => {
    if (!exec.result) return;

    setSteps((prev) => {
      return prev.map((step) => {
        const stepOutput = exec.result[`${step.name}_output`] || exec.result[`${step.name}_result`];

        if (stepOutput) {
          return {
            ...step,
            status: 'completed' as const,
            result: stepOutput,
          };
        }

        if (exec.result.error && exec.result.failed_node === step.name) {
          return {
            ...step,
            status: 'failed' as const,
            error: exec.result.error,
          };
        }

        // 检查是否正在执行（通过 execution_history）
        if (exec.result.execution_history) {
          const historyEntry = exec.result.execution_history.find(
            (h: any) => h.node_id === step.name
          );
          if (historyEntry) {
            return {
              ...step,
              status: 'completed' as const,
              result: historyEntry.response,
            };
          }
        }

        return step;
      });
    });
  };

  const getStatusIcon = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'running':
        return '⏳';
      case 'failed':
        return '❌';
      default:
        return '⏸️';
    }
  };

  const getStatusColor = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="p-3 bg-gray-50 rounded-lg">
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  const completedSteps = steps.filter((s) => s.status === 'completed').length;
  const totalSteps = steps.length;
  const calculatedProgress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;
  const displayProgress = progress !== undefined ? progress : calculatedProgress;

  return (
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-900">
              {workflow?.name || '工作流执行'}
            </h4>
            <p className="text-xs text-gray-500">
              {executing ? '执行中...' : execution?.success ? '执行完成' : '执行失败'}
            </p>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg
            className={`w-5 h-5 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* 进度条 */}
      {executing && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>
              进度: {completedSteps}/{totalSteps}
            </span>
            <span>{Math.round(displayProgress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${displayProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* 步骤列表 */}
      {expanded && (
        <div className="space-y-2 mt-3">
          {steps.length === 0 ? (
            <p className="text-sm text-gray-500">暂无步骤信息</p>
          ) : (
            steps.map((step, index) => (
              <div key={step.id} className="flex gap-2 items-start">
                <span className={`text-sm ${getStatusColor(step.status)} mt-0.5`}>
                  {getStatusIcon(step.status)}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-medium ${getStatusColor(step.status)}`}>
                      {step.name}
                    </span>
                    <span className="text-xs text-gray-500 capitalize">{step.status}</span>
                  </div>
                  <p className="text-xs text-gray-500">{step.type}</p>

                  {/* 步骤结果 */}
                  {step.result && step.status === 'completed' && (
                    <div className="mt-1 p-2 bg-white rounded text-xs border border-gray-200">
                      <div className="text-gray-600 font-medium mb-1">结果:</div>
                      <div className="text-gray-800 whitespace-pre-wrap break-words">
                        {typeof step.result === 'string'
                          ? step.result
                          : typeof step.result === 'object' && step.result.content
                            ? step.result.content
                            : JSON.stringify(step.result, null, 2)}
                      </div>
                    </div>
                  )}

                  {/* 错误信息 */}
                  {step.error && (
                    <div className="mt-1 p-2 bg-red-50 rounded text-xs text-red-600 border border-red-200">
                      {step.error}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 执行结果摘要 */}
      {execution && !executing && (
        <div
          className={`mt-3 p-3 rounded-lg ${
            execution.success
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className="flex items-center justify-between">
            <span
              className={`text-sm font-medium ${
                execution.success ? 'text-green-800' : 'text-red-800'
              }`}
            >
              {execution.success ? '✅ 执行成功' : '❌ 执行失败'}
            </span>
            {execution.execution_time && (
              <span className="text-xs text-gray-600">
                耗时:{' '}
                {typeof execution.execution_time === 'number'
                  ? execution.execution_time.toFixed(2)
                  : execution.execution_time}
                s
              </span>
            )}
          </div>
          {execution.error && <p className="text-sm text-red-600 mt-2">{execution.error}</p>}
        </div>
      )}
    </div>
  );
};
