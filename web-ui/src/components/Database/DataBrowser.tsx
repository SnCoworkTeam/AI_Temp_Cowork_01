'use client';

import React, { useState, useEffect } from 'react';
import {
  Table as TableIcon,
  Search,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Download,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Card } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { getAccessToken } from '@/lib/auth';

interface TableInfo {
  name: string;
  schema: string;
  rowCount: number;
  size: number;
  columns: ColumnInfo[];
}

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  isPrimaryKey: boolean;
}

interface DataBrowserProps {
  onSelectTable?: (tableName: string) => void;
  onViewData?: (tableName: string) => void;
}

export function DataBrowser({ onSelectTable, onViewData }: DataBrowserProps) {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [showSensitiveData, setShowSensitiveData] = useState(false);

  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    try {
      setLoading(true);
      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch('/api/admin/database/tables', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch tables');
      }

      const data = await response.json();
      setTables(data.tables || []);
    } catch (error) {
      console.error('Error fetching tables:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleTable = (tableName: string) => {
    const newExpanded = new Set(expandedTables);
    if (newExpanded.has(tableName)) {
      newExpanded.delete(tableName);
    } else {
      newExpanded.add(tableName);
    }
    setExpandedTables(newExpanded);
  };

  const handleSelectTable = (tableName: string) => {
    setSelectedTable(tableName);
    onSelectTable?.(tableName);
  };

  const handleViewData = (tableName: string) => {
    onViewData?.(tableName);
  };

  const filteredTables = tables.filter(
    (table) =>
      table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      table.schema.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const isSensitiveColumn = (columnName: string) => {
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
    return sensitiveKeywords.some((keyword) => columnName.toLowerCase().includes(keyword));
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">数据表浏览器</h2>
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
          <Button variant="outline" size="sm" onClick={fetchTables}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* 搜索框 */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <Input
            type="text"
            placeholder="搜索数据表..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* 数据表列表 */}
      <div className="space-y-2">
        {filteredTables.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">没有找到数据表</div>
        ) : (
          filteredTables.map((table) => {
            const isExpanded = expandedTables.has(table.name);
            const isSelected = selectedTable === table.name;

            return (
              <div
                key={table.name}
                className={`
                  border rounded-lg transition-colors
                  ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
                  }
                `}
              >
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
                  onClick={() => handleSelectTable(table.name)}
                >
                  <div className="flex items-center flex-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleTable(table.name);
                      }}
                      className="mr-2 p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                    <TableIcon className="w-5 h-5 mr-3 text-gray-500 dark:text-gray-400" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {table.name}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {table.schema}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {table.rowCount.toLocaleString()} 行 · {formatBytes(table.size)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewData(table.name);
                      }}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* 列信息 */}
                {isExpanded && (
                  <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      列信息
                    </div>
                    <div className="space-y-1">
                      {table.columns.map((column) => {
                        const isSensitive = isSensitiveColumn(column.name);

                        return (
                          <div
                            key={column.name}
                            className="flex items-center justify-between text-sm py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                          >
                            <div className="flex items-center gap-2">
                              {column.isPrimaryKey && (
                                <span className="px-1.5 py-0.5 text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded">
                                  PK
                                </span>
                              )}
                              <span className="font-medium text-gray-900 dark:text-white">
                                {column.name}
                              </span>
                              {isSensitive && !showSensitiveData && (
                                <span className="text-xs text-red-600 dark:text-red-400">
                                  (敏感)
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                              <span className="text-xs">{column.type}</span>
                              {!column.nullable && (
                                <span className="text-xs font-medium text-red-600 dark:text-red-400">
                                  NOT NULL
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
