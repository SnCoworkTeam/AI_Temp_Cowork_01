'use client';

import React, { useState, useMemo } from 'react';
import {
  Database,
  FileText,
  Workflow,
  Bot,
  Building2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Filter,
  Search,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  extractUniqueClassifications,
  extractClassification,
  normalizeClassification,
  getClassificationDisplayName,
} from '@/lib/metadata-classification';

interface MetadataItem {
  id: string | number;
  name: string;
  display_name?: string;
  description?: string;
  type?: string;
  asset_type?: string;
  status?: string;
  classification?: string;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  [key: string]: any;
}

type MetadataType = 'all' | 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

interface EnhancedListViewProps {
  items: MetadataItem[];
  type: MetadataType;
  onItemClick?: (item: MetadataItem) => void;
  loading?: boolean;
  emptyMessage?: string;
}

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
};

export function EnhancedListView({
  items,
  type,
  onItemClick,
  loading = false,
  emptyMessage = '暂无数据',
}: EnhancedListViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [classificationFilter, setClassificationFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'created_at' | 'updated_at'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // 获取所有唯一的分类和状态值
  const classifications = useMemo(() => {
    // 使用分类工具提取分类，支持多种数据源
    const extracted = extractUniqueClassifications(items, type);
    // 如果没有提取到分类，返回空数组（不显示筛选）
    return extracted.length > 0 ? extracted : [];
  }, [items, type]);

  const statuses = useMemo(() => {
    const set = new Set<string>();
    items.forEach((item) => {
      if (item.status) set.add(item.status);
    });
    return Array.from(set).sort();
  }, [items]);

  // 过滤和排序数据
  const filteredAndSortedItems = useMemo(() => {
    let filtered = [...items];

    // 搜索过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((item) => {
        const name = (item.display_name || item.name || '').toLowerCase();
        const desc = (item.description || '').toLowerCase();
        const classification = item.classification
          ? getClassificationDisplayName(item.classification, type).toLowerCase()
          : '';
        return name.includes(query) || desc.includes(query) || classification.includes(query);
      });
    }

    // 状态过滤
    if (statusFilter !== 'all') {
      filtered = filtered.filter((item) => item.status === statusFilter);
    }

    // 分类过滤（支持标准化后的分类值匹配）
    if (classificationFilter !== 'all') {
      filtered = filtered.filter((item) => {
        // 提取并标准化分类值进行匹配
        const extracted = extractClassification(item, type);
        const normalized = normalizeClassification(extracted, type);
        return normalized === classificationFilter;
      });
    }

    // 排序
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case 'name':
          aValue = a.display_name || a.name || '';
          bValue = b.display_name || b.name || '';
          break;
        case 'created_at':
          aValue = a.created_at ? new Date(a.created_at).getTime() : 0;
          bValue = b.created_at ? new Date(b.created_at).getTime() : 0;
          break;
        case 'updated_at':
          aValue = a.updated_at ? new Date(a.updated_at).getTime() : 0;
          bValue = b.updated_at ? new Date(b.updated_at).getTime() : 0;
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
      }
    });

    return filtered;
  }, [items, searchQuery, statusFilter, classificationFilter, sortBy, sortOrder]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 搜索和筛选工具栏 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col gap-4">
          {/* 搜索框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="搜索名称、描述、分类..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 筛选面板切换 */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-300"
            >
              <Filter className="w-4 h-4" />
              筛选
              {showFilters ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {/* 排序 */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">排序:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm"
              >
                <option value="name">名称</option>
                <option value="created_at">创建时间</option>
                <option value="updated_at">更新时间</option>
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                title={sortOrder === 'asc' ? '升序' : '降序'}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>

          {/* 筛选面板 */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
              {/* 状态筛选 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">状态</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                >
                  <option value="all">全部</option>
                  {statuses.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </div>

              {/* 分类筛选 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">分类</label>
                <select
                  value={classificationFilter}
                  onChange={(e) => setClassificationFilter(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                >
                  <option value="all">全部</option>
                  {classifications.map((classification) => (
                    <option key={classification} value={classification}>
                      {getClassificationDisplayName(classification, type)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* 结果统计 */}
        <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
          显示 {filteredAndSortedItems.length} / {items.length} 条结果
        </div>
      </div>

      {/* 列表内容 */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  分类
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  创建时间
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedItems.map((item) => (
                <tr
                  key={`${type}-${item.id}`}
                  onClick={() => onItemClick?.(item)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center text-gray-400">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {item.display_name || item.name}
                        </div>
                        {item.description && (
                          <div className="text-sm text-gray-500 line-clamp-1 max-w-md">
                            {item.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {item.classification && (
                      <span className="px-2 py-1 text-xs rounded bg-blue-50 text-blue-700 border border-blue-200">
                        {getClassificationDisplayName(item.classification, type)}
                      </span>
                    )}
                    {item.asset_type && (
                      <span className="ml-2 px-2 py-1 text-xs rounded bg-gray-50 text-gray-700 border border-gray-200">
                        {item.asset_type}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {item.status && (
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          item.status === 'active'
                            ? 'bg-green-50 text-green-700 border border-green-200'
                            : item.status === 'inactive'
                              ? 'bg-gray-50 text-gray-700 border border-gray-200'
                              : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                        }`}
                      >
                        {item.status}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(item.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onItemClick?.(item);
                      }}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      查看
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
