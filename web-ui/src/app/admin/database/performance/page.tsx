'use client';

import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Clock, Database } from 'lucide-react';
import { Card } from '@/components/UI/Card';
import { PerformanceCharts } from '@/components/Database/PerformanceCharts';
import { getAccessToken } from '@/lib/auth';

interface PerformanceMetrics {
  activeConnections: number;
  queryCount: number;
  avgQueryTime: number;
  slowQueries: number;
  cacheHitRate: number;
  tableSizes: Array<{ name: string; size: number }>;
  indexUsage: Array<{ name: string; usage: number }>;
}

export default function DatabasePerformancePage() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('1h');

  useEffect(() => {
    fetchPerformanceMetrics();
    const interval = setInterval(fetchPerformanceMetrics, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, [timeRange]);

  const fetchPerformanceMetrics = async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch(`/api/admin/database/performance?timeRange=${timeRange}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">性能监控</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">实时监控数据库性能指标</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="1h">最近1小时</option>
          <option value="6h">最近6小时</option>
          <option value="24h">最近24小时</option>
          <option value="7d">最近7天</option>
        </select>
      </div>

      {/* 关键指标 */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">活跃连接数</p>
                <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.activeConnections}
                </p>
              </div>
              <Activity className="w-12 h-12 text-blue-600 dark:text-blue-400" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">查询总数</p>
                <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.queryCount.toLocaleString()}
                </p>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                  慢查询: {metrics.slowQueries}
                </p>
              </div>
              <TrendingUp className="w-12 h-12 text-green-600 dark:text-green-400" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">平均查询时间</p>
                <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.avgQueryTime.toFixed(2)}ms
                </p>
              </div>
              <Clock className="w-12 h-12 text-purple-600 dark:text-purple-400" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">缓存命中率</p>
                <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                  {(metrics.cacheHitRate * 100).toFixed(1)}%
                </p>
              </div>
              <Database className="w-12 h-12 text-orange-600 dark:text-orange-400" />
            </div>
          </Card>
        </div>
      )}

      {/* 性能图表 */}
      <PerformanceCharts timeRange={timeRange} />

      {/* 表大小统计 */}
      {metrics && metrics.tableSizes.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">表大小统计</h2>
          <div className="space-y-2">
            {metrics.tableSizes.slice(0, 10).map((table) => (
              <div
                key={table.name}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <span className="font-medium text-gray-900 dark:text-white">{table.name}</span>
                <span className="text-gray-600 dark:text-gray-400">{formatBytes(table.size)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
