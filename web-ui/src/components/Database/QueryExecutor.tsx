'use client';

import React, { useState } from 'react';
import { Play, Save, Download, AlertCircle, CheckCircle, Loader2, Eye, EyeOff } from 'lucide-react';
import { Card } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { getAccessToken } from '@/lib/auth';
import { Modal } from '@/components/UI/Modal';

interface QueryExecutorProps {
  initialTable?: string | null;
}

interface QueryResult {
  columns: string[];
  rows: any[][];
  rowCount: number;
  executionTime: number;
}

export function QueryExecutor({ initialTable }: QueryExecutorProps) {
  const [query, setQuery] = useState(
    initialTable ? `SELECT * FROM ${initialTable} LIMIT 100;` : ''
  );
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSensitiveData, setShowSensitiveData] = useState(false);
  const [confirmModal, setConfirmModal] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);

  const isDangerousQuery = (sql: string): boolean => {
    const dangerousKeywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE'];
    const upperSql = sql.trim().toUpperCase();
    return dangerousKeywords.some((keyword) => upperSql.startsWith(keyword));
  };

  const executeQuery = async (sqlQuery: string) => {
    if (!sqlQuery.trim()) {
      setError('请输入SQL查询');
      return;
    }

    // 检查危险操作
    if (isDangerousQuery(sqlQuery)) {
      setPendingQuery(sqlQuery);
      setConfirmModal(true);
      return;
    }

    await doExecuteQuery(sqlQuery);
  };

  const doExecuteQuery = async (sqlQuery: string) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch('/api/admin/database/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query: sqlQuery }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || '查询执行失败');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '查询执行失败');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (pendingQuery) {
      doExecuteQuery(pendingQuery);
      setPendingQuery(null);
    }
    setConfirmModal(false);
  };

  const exportResult = () => {
    if (!result) return;

    const csv = [
      result.columns.join(','),
      ...result.rows.map((row) => row.map((cell) => `"${cell || ''}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_result_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const maskSensitiveData = (value: any, columnName: string): string => {
    if (!value) return '';
    const sensitiveKeywords = [
      'password',
      'token',
      'secret',
      'key',
      'email',
      'phone',
      'id_card',
      'credit_card',
    ];
    const isSensitive = sensitiveKeywords.some((keyword) =>
      columnName.toLowerCase().includes(keyword)
    );

    if (isSensitive && !showSensitiveData) {
      const str = String(value);
      if (str.length <= 4) return '****';
      return str.substring(0, 2) + '****' + str.substring(str.length - 2);
    }
    return String(value);
  };

  return (
    <>
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">SQL查询执行器</h2>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSensitiveData(!showSensitiveData)}
            >
              {showSensitiveData ? (
                <>
                  <EyeOff className="w-4 h-4 mr-2" />
                  隐藏敏感数据
                </>
              ) : (
                <>
                  <Eye className="w-4 h-4 mr-2" />
                  显示敏感数据
                </>
              )}
            </Button>
          </div>
        </div>

        {/* SQL编辑器 */}
        <div className="mb-4">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full h-48 p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入SQL查询语句..."
          />
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-2 mb-4">
          <Button onClick={() => executeQuery(query)} disabled={loading} variant="primary">
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                执行中...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                执行查询
              </>
            )}
          </Button>
          {result && (
            <Button variant="outline" onClick={exportResult}>
              <Download className="w-4 h-4 mr-2" />
              导出结果
            </Button>
          )}
        </div>

        {/* 错误信息 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2" />
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        )}

        {/* 查询结果 */}
        {result && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span>
                  查询成功 · {result.rowCount} 行 · {result.executionTime.toFixed(2)}ms
                </span>
              </div>
            </div>
            <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    {result.columns.map((col, idx) => (
                      <th
                        key={idx}
                        className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {result.rows.slice(0, 1000).map((row, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      {row.map((cell, cellIdx) => (
                        <td
                          key={cellIdx}
                          className="px-4 py-2 text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700"
                        >
                          {maskSensitiveData(cell, result.columns[cellIdx])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {result.rows.length > 1000 && (
                <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800">
                  显示前1000行，共{result.rowCount}行
                </div>
              )}
            </div>
          </div>
        )}
      </Card>

      {/* 确认对话框 */}
      <Modal
        isOpen={confirmModal}
        onClose={() => {
          setConfirmModal(false);
          setPendingQuery(null);
        }}
        title="确认执行危险操作"
      >
        <div className="space-y-4">
          <div className="flex items-start">
            <AlertCircle className="w-6 h-6 text-yellow-600 dark:text-yellow-400 mr-3 mt-0.5" />
            <div>
              <p className="text-gray-900 dark:text-white font-medium mb-2">
                警告：这是一个危险操作
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                您即将执行一个可能修改或删除数据的操作。此操作不可撤销。
              </p>
              <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg font-mono text-xs text-gray-800 dark:text-gray-200">
                {pendingQuery}
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setConfirmModal(false);
                setPendingQuery(null);
              }}
            >
              取消
            </Button>
            <Button variant="destructive" onClick={handleConfirm}>
              确认执行
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
