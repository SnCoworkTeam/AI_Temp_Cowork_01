'use client';

import React, { useState, useEffect } from 'react';
import {
  HardDrive,
  Download,
  Trash2,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  Settings,
} from 'lucide-react';
import { Card } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { BackupManager } from '@/components/Database/BackupManager';
import { getAccessToken } from '@/lib/auth';

interface BackupConfig {
  id: string;
  name: string;
  schedule: string;
  retention: number;
  enabled: boolean;
  lastRun: string | null;
  nextRun: string | null;
}

export default function DatabaseBackupsPage() {
  const [backups, setBackups] = useState<any[]>([]);
  const [configs, setConfigs] = useState<BackupConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showConfigModal, setShowConfigModal] = useState(false);

  useEffect(() => {
    fetchBackups();
    fetchBackupConfigs();
  }, []);

  const fetchBackups = async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch('/api/admin/database/backups', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBackups(data.backups || []);
      }
    } catch (error) {
      console.error('Error fetching backups:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBackupConfigs = async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch('/api/admin/database/backups/configs', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConfigs(data.configs || []);
      }
    } catch (error) {
      console.error('Error fetching backup configs:', error);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '未执行';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">备份管理</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">管理数据库备份和自动备份配置</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowConfigModal(true)}>
            <Settings className="w-4 h-4 mr-2" />
            备份配置
          </Button>
          <Button
            variant="primary"
            onClick={async () => {
              // 触发手动备份
              const token = getAccessToken();
              if (token) {
                await fetch('/api/admin/database/backups/create', {
                  method: 'POST',
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                });
                fetchBackups();
              }
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            创建备份
          </Button>
        </div>
      </div>

      {/* 自动备份配置 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">自动备份配置</h2>
        {configs.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            暂无自动备份配置
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => setShowConfigModal(true)}
            >
              创建配置
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {configs.map((config) => (
              <div
                key={config.id}
                className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900 dark:text-white">{config.name}</h3>
                    {config.enabled ? (
                      <span className="px-2 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
                        已启用
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded">
                        已禁用
                      </span>
                    )}
                  </div>
                  <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    <div>计划: {config.schedule}</div>
                    <div>保留天数: {config.retention} 天</div>
                    <div>上次执行: {formatDate(config.lastRun)}</div>
                    <div>下次执行: {formatDate(config.nextRun)}</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    编辑
                  </Button>
                  <Button variant="ghost" size="sm">
                    删除
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 备份列表 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">备份列表</h2>
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : backups.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">暂无备份记录</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white">
                    备份名称
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white">
                    大小
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white">
                    创建时间
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white">
                    状态
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {backups.map((backup) => (
                  <tr key={backup.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3 text-gray-900 dark:text-white">{backup.name}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {formatBytes(backup.size)}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {formatDate(backup.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      {backup.status === 'completed' ? (
                        <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                          <CheckCircle className="w-4 h-4" />
                          完成
                        </span>
                      ) : backup.status === 'failed' ? (
                        <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
                          <AlertCircle className="w-4 h-4" />
                          失败
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                          <Clock className="w-4 h-4" />
                          进行中
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm">
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* 备份管理器组件 */}
      <BackupManager
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        onSave={fetchBackupConfigs}
      />
    </div>
  );
}
