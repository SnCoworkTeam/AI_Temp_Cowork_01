'use client';

import { useEffect, useState } from 'react';
import { ToolExecutionStatus } from '@/types/chat';

interface ToolExecutionProps {
  executionId: string;
  toolName: string;
  status?: ToolExecutionStatus;
}

export function ToolExecution({ executionId, toolName, status: propStatus }: ToolExecutionProps) {
  const [status, setStatus] = useState<ToolExecutionStatus | null>(propStatus || null);
  const [loading, setLoading] = useState(!propStatus);

  useEffect(() => {
    if (propStatus) {
      setStatus(propStatus);
      setLoading(false);
      return;
    }

    // 如果没有传入状态，使用模拟数据
    const mockStatus: ToolExecutionStatus = {
      toolName,
      executionId,
      status: 'running',
      startTime: Date.now() - 2000,
    };
    setStatus(mockStatus);
    setLoading(false);

    // 模拟完成
    setTimeout(() => {
      setStatus({
        ...mockStatus,
        status: 'completed',
        result: { success: true, data: '执行结果' },
        endTime: Date.now(),
      });
    }, 3000);
  }, [executionId, toolName, propStatus]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span>执行中...</span>
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
  };

  const statusText = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">工具: {toolName}</span>
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded ${statusColors[status.status]}`}
          >
            {statusText[status.status]}
          </span>
        </div>
        {status.status === 'running' && (
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        )}
      </div>

      {/* 执行结果 */}
      {status.status === 'completed' && status.result && (
        <div className="text-xs bg-gray-50 p-2 rounded border border-gray-200">
          <div className="font-medium mb-1">执行结果:</div>
          <pre className="whitespace-pre-wrap text-xs">
            {typeof status.result === 'string'
              ? status.result
              : JSON.stringify(status.result, null, 2)}
          </pre>
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
