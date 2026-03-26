'use client';

import React, { useState } from 'react';
import { Modal } from '@/components/UI/Modal';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { getAccessToken } from '@/lib/auth';

interface BackupManagerProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
}

export function BackupManager({ isOpen, onClose, onSave }: BackupManagerProps) {
  const [name, setName] = useState('');
  const [schedule, setSchedule] = useState('daily');
  const [retention, setRetention] = useState(30);
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    try {
      setLoading(true);
      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch('/api/admin/database/backups/configs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          schedule,
          retention,
          enabled,
        }),
      });

      if (response.ok) {
        onSave();
        onClose();
        // 重置表单
        setName('');
        setSchedule('daily');
        setRetention(30);
        setEnabled(true);
      }
    } catch (error) {
      console.error('Error saving backup config:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="备份配置">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            配置名称
          </label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如: 每日备份"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            备份计划
          </label>
          <select
            value={schedule}
            onChange={(e) => setSchedule(e.target.value)}
            className="w-full h-10 px-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="hourly">每小时</option>
            <option value="daily">每天</option>
            <option value="weekly">每周</option>
            <option value="monthly">每月</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            保留天数
          </label>
          <Input
            type="number"
            value={retention}
            onChange={(e) => setRetention(parseInt(e.target.value))}
            min={1}
            max={365}
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="enabled"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label
            htmlFor="enabled"
            className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            启用自动备份
          </label>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={loading}>
            {loading ? '保存中...' : '保存'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
