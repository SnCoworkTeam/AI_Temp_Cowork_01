'use client';

import { useEffect, useState } from 'react';
import { WorkflowExecutionStatus } from '@/types/chat';

interface WorkflowStatusProps {
  executionId: string;
  workflowName: string;
  status?: WorkflowExecutionStatus;
}

export function WorkflowStatus({
  executionId,
  workflowName,
  status: propStatus,
}: WorkflowStatusProps) {
  const [status, setStatus] = useState<WorkflowExecutionStatus | null>(propStatus || null);
  const [loading, setLoading] = useState(!propStatus);

  useEffect(() => {
    if (propStatus) {
      setStatus(propStatus);
      setLoading(false);
      return;
    }

    // 如果没有传入状态，使用模拟数据
    const mockStatus: WorkflowExecutionStatus = {
      executionId,
      workflowId: '',
      workflowName,
      status: 'running',
      progress: 50,
      currentNode: 'analyze',
      startTime: Date.now() - 5000,
    };
    setStatus(mockStatus);
    setLoading(false);

    // 模拟完成
    setTimeout(() => {
      setStatus({
        ...mockStatus,
        status: 'completed',
        progress: 100,
        endTime: Date.now(),
      });
    }, 5000);
  }, [executionId, workflowName, propStatus]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span>加载中...</span>
      </div>
    );
  }

  if (!status) {
    return <div className="text-sm text-gray-500">状态不可用</div>;
  }

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  };

  const statusText = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">工作流: {workflowName}</span>
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded ${statusColors[status.status]}`}
          >
            {statusText[status.status]}
          </span>
        </div>
        {status.progress !== undefined && (
          <span className="text-xs text-gray-500">{status.progress}%</span>
        )}
      </div>

      {/* 进度条 */}
      {status.status === 'running' && status.progress !== undefined && (
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${status.progress}%` }}
          />
        </div>
      )}

      {/* 当前节点 */}
      {status.currentNode && (
        <div className="text-xs text-gray-600">
          当前节点: <span className="font-medium">{status.currentNode}</span>
        </div>
      )}

      {/* 错误信息 */}
      {status.error && (
        <div className="text-xs text-red-600 bg-red-50 p-2 rounded">{status.error}</div>
      )}

      {/* 执行时间 */}
      {status.endTime && (
        <div className="text-xs text-gray-500">
          执行时间: {((status.endTime - status.startTime) / 1000).toFixed(2)}秒
        </div>
      )}
    </div>
  );
}
