'use client';

import React, { useState, useEffect } from 'react';
import { Database, Activity, HardDrive, Users, TrendingUp, AlertCircle, Table } from 'lucide-react';
import { Card } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { getAccessToken } from '@/lib/auth';

interface DatabaseStats {
  totalSize: number;
  usedSize: number;
  connectionCount: number;
  activeQueries: number;
  tableCount: number;
  indexCount: number;
  lastBackup: string | null;
  healthStatus: 'healthy' | 'warning' | 'critical';
}

export default function DatabaseOverviewPage() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatabaseStats();
  }, []);

  const fetchDatabaseStats = async () => {
    try {
      setLoading(true);
      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch('/api/admin/database/stats', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch database stats');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
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

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2" />
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const usagePercentage = (stats.usedSize / stats.totalSize) * 100;

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">数据库概览</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">查看数据库整体状态和关键指标</p>
      </div>

      {/* 健康状态 */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">数据库状态</h3>
            <p className={`text-sm font-medium ${getHealthStatusColor(stats.healthStatus)}`}>
              {stats.healthStatus === 'healthy'
                ? '运行正常'
                : stats.healthStatus === 'warning'
                  ? '警告'
                  : '严重问题'}
            </p>
          </div>
          <Button onClick={fetchDatabaseStats} variant="outline" size="sm">
            刷新
          </Button>
        </div>
      </Card>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">数据库大小</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {formatBytes(stats.totalSize)}
              </p>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                已使用: {formatBytes(stats.usedSize)} ({usagePercentage.toFixed(1)}%)
              </p>
            </div>
            <Database className="w-12 h-12 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  usagePercentage > 80
                    ? 'bg-red-600'
                    : usagePercentage > 60
                      ? 'bg-yellow-600'
                      : 'bg-green-600'
                }`}
                style={{ width: `${usagePercentage}%` }}
              ></div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">数据表数量</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {stats.tableCount}
              </p>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                索引: {stats.indexCount}
              </p>
            </div>
            <Table className="w-12 h-12 text-green-600 dark:text-green-400" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">连接数</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {stats.connectionCount}
              </p>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                活跃查询: {stats.activeQueries}
              </p>
            </div>
            <Users className="w-12 h-12 text-purple-600 dark:text-purple-400" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">最后备份</p>
              <p className="mt-2 text-lg font-semibold text-gray-900 dark:text-white">
                {stats.lastBackup ? new Date(stats.lastBackup).toLocaleString('zh-CN') : '未备份'}
              </p>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                {stats.lastBackup
                  ? `${Math.floor(
                      (Date.now() - new Date(stats.lastBackup).getTime()) / (1000 * 60 * 60)
                    )} 小时前`
                  : '建议立即备份'}
              </p>
            </div>
            <HardDrive className="w-12 h-12 text-orange-600 dark:text-orange-400" />
          </div>
        </Card>
      </div>

      {/* 快速操作 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">快速操作</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button
            variant="outline"
            className="w-full"
            onClick={() => (window.location.href = '/admin/database/backups')}
          >
            <HardDrive className="w-4 h-4 mr-2" />
            创建备份
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => (window.location.href = '/admin/database/tables')}
          >
            <Table className="w-4 h-4 mr-2" />
            管理数据表
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => (window.location.href = '/admin/database/performance')}
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            查看性能
          </Button>
        </div>
      </Card>
    </div>
  );
}
