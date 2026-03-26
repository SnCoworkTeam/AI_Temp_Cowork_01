'use client';

import { useState, useEffect } from 'react';
import { LogEntry, LogQueryParams, queryLogs } from '@/lib/api/monitoring';

interface LogViewerProps {
  service?: string;
  refreshInterval?: number;
}

export function LogViewer({ service, refreshInterval = 10000 }: LogViewerProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<LogQueryParams>({
    service: service,
    level: undefined,
    keyword: undefined,
    limit: 100,
    offset: 0,
  });

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await queryLogs(filters);
      setLogs(response.logs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, refreshInterval);
    return () => clearInterval(interval);
  }, [filters, refreshInterval]);

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'info':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'debug':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const handleFilterChange = (key: keyof LogQueryParams, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 过滤器 */}
      <div className="p-4 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">服务</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filters.service || ''}
              onChange={(e) => handleFilterChange('service', e.target.value || undefined)}
            >
              <option value="">全部</option>
              <option value="mcp-gateway">MCP Gateway</option>
              <option value="workflow-engine">Workflow Engine</option>
              <option value="auth-service">Auth Service</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">级别</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filters.level || ''}
              onChange={(e) => handleFilterChange('level', e.target.value || undefined)}
            >
              <option value="">全部</option>
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">关键词</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="搜索日志..."
              value={filters.keyword || ''}
              onChange={(e) => handleFilterChange('keyword', e.target.value || undefined)}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchLogs}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              刷新
            </button>
          </div>
        </div>
      </div>

      {/* 日志列表 */}
      <div className="p-4">
        {loading && logs.length === 0 ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">加载日志中...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-red-600">{error}</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">暂无日志</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs.map((log, idx) => (
              <div key={idx} className={`p-3 rounded border-l-4 ${getLevelColor(log.level)}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold">{log.level}</span>
                      <span className="text-xs text-gray-500">{log.service}</span>
                      <span className="text-xs text-gray-500">{log.logger}</span>
                    </div>
                    <p className="text-sm">{log.message}</p>
                    {log.traceback && (
                      <details className="mt-2">
                        <summary className="text-xs text-gray-500 cursor-pointer">堆栈跟踪</summary>
                        <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                          {log.traceback}
                        </pre>
                      </details>
                    )}
                    {Object.keys(log.context).length > 0 && (
                      <div className="mt-2">
                        <details>
                          <summary className="text-xs text-gray-500 cursor-pointer">上下文</summary>
                          <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(log.context, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 ml-4 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
