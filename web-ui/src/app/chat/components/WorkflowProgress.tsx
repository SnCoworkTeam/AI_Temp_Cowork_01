'use client';

import React, { useState, useEffect } from 'react';
import { getWorkflow } from '@/lib/api/workflow';

interface WorkflowProgressProps {
  workflowId: string;
  execution?: any;
  executing?: boolean;
  onStepInteraction?: (stepId: string, action: string, data?: any) => void;
  onClose?: () => void;
}

interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

export const WorkflowProgress: React.FC<WorkflowProgressProps> = ({
  workflowId,
  execution,
  executing,
  onStepInteraction,
  onClose,
}) => {
  const [workflow, setWorkflow] = useState<any>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [loading, setLoading] = useState(true);

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

      // 从工作流定义中提取步骤
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
        // 检查执行结果中是否有该步骤的输出
        const stepOutput = exec.result[`${step.name}_output`] || exec.result[`${step.name}_result`];

        if (stepOutput) {
          return {
            ...step,
            status: 'completed' as const,
            result: stepOutput,
          };
        }

        // 检查是否有错误
        if (exec.result.error && exec.result.failed_node === step.name) {
          return {
            ...step,
            status: 'failed' as const,
            error: exec.result.error,
          };
        }

        return step;
      });
    });
  };

  const getStatusIcon = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return (
          <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        );
      case 'running':
        return (
          <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          </div>
        );
      case 'failed':
        return (
          <div className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-gray-400"></div>
          </div>
        );
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
      <div className="p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{workflow?.name || '工作流执行'}</h3>
          {executing && <p className="text-xs text-gray-500 mt-1">执行中...</p>}
        </div>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* 步骤列表 */}
      <div className="flex-1 overflow-y-auto p-4">
        {steps.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-sm">暂无步骤信息</p>
          </div>
        ) : (
          <div className="space-y-4">
            {steps.map((step, index) => (
              <div key={step.id} className="flex gap-3">
                {/* 状态图标 */}
                <div className="flex flex-col items-center">
                  {getStatusIcon(step.status)}
                  {index < steps.length - 1 && (
                    <div
                      className={`w-0.5 h-8 mt-2 ${
                        step.status === 'completed' ? 'bg-green-200' : 'bg-gray-200'
                      }`}
                    ></div>
                  )}
                </div>

                {/* 步骤信息 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className={`text-sm font-medium ${getStatusColor(step.status)}`}>
                      {step.name}
                    </h4>
                    <span className="text-xs text-gray-500 capitalize">{step.status}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{step.type}</p>

                  {/* 步骤结果 */}
                  {step.result && (
                    <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                      <pre className="whitespace-pre-wrap break-words">
                        {typeof step.result === 'string'
                          ? step.result
                          : JSON.stringify(step.result, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* 错误信息 */}
                  {step.error && (
                    <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-600">
                      {step.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 执行结果摘要 */}
        {execution && execution.result && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">执行结果</h4>
            <div className="text-xs text-blue-800">
              {execution.success ? (
                <p className="text-green-600">✅ 执行成功</p>
              ) : (
                <p className="text-red-600">❌ 执行失败</p>
              )}
              {execution.execution_id && <p className="mt-1">执行ID: {execution.execution_id}</p>}
              {execution.execution_time && (
                <p className="mt-1">
                  耗时:{' '}
                  {typeof execution.execution_time === 'number'
                    ? execution.execution_time.toFixed(2)
                    : execution.execution_time}
                  s
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
