'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  Edit2,
  Check,
  X,
  Download,
  Trash2,
  Plus,
  Search,
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Info,
} from 'lucide-react';

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
  [key: string]: any;
}

type MetadataType = 'all' | 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

interface EditableTableViewProps {
  items: MetadataItem[];
  type: MetadataType;
  onItemClick?: (item: MetadataItem) => void;
  onItemUpdate?: (item: MetadataItem) => void;
  onItemDelete?: (item: MetadataItem) => void;
  onBatchDelete?: (items: MetadataItem[]) => void;
  loading?: boolean;
  emptyMessage?: string;
  editable?: boolean;
}

type SortField = 'name' | 'display_name' | 'type' | 'status' | 'created_at';
type SortOrder = 'asc' | 'desc' | null;

export function EditableTableView({
  items,
  type,
  onItemClick,
  onItemUpdate,
  onItemDelete,
  onBatchDelete,
  loading = false,
  emptyMessage = '暂无数据',
  editable = true,
}: EditableTableViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [selectedItems, setSelectedItems] = useState<Set<string | number>>(new Set());
  const [editingCell, setEditingCell] = useState<{ rowId: string | number; field: string } | null>(
    null
  );
  const [editValue, setEditValue] = useState<string>('');

  // 获取所有类型（用于筛选）
  const allTypes = useMemo(() => {
    const types = new Set<string>();
    items.forEach((item) => {
      if (item.type) types.add(item.type);
      if (item.asset_type) types.add(item.asset_type);
    });
    return Array.from(types).sort();
  }, [items]);

  // 过滤和排序数据
  const filteredAndSortedItems = useMemo(() => {
    let filtered = items;

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((item) => {
        const name = (item.display_name || item.name || '').toLowerCase();
        const desc = (item.description || '').toLowerCase();
        return name.includes(query) || desc.includes(query);
      });
    }

    // 类型过滤
    if (filterType !== 'all') {
      filtered = filtered.filter(
        (item) => item.type === filterType || item.asset_type === filterType
      );
    }

    // 排序
    if (sortField && sortOrder) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortField] || '';
        const bValue = b[sortField] || '';
        const comparison = String(aValue).localeCompare(String(bValue), 'zh-CN');
        return sortOrder === 'asc' ? comparison : -comparison;
      });
    }

    return filtered;
  }, [items, searchQuery, filterType, sortField, sortOrder]);

  // 处理排序
  const handleSort = useCallback(
    (field: SortField) => {
      if (sortField === field) {
        // 切换排序顺序：asc -> desc -> null -> asc
        if (sortOrder === 'asc') {
          setSortOrder('desc');
        } else if (sortOrder === 'desc') {
          setSortOrder(null);
          setSortField('name');
        } else {
          setSortOrder('asc');
        }
      } else {
        setSortField(field);
        setSortOrder('asc');
      }
    },
    [sortField, sortOrder]
  );

  // 获取排序图标
  const getSortIcon = useCallback(
    (field: SortField) => {
      if (sortField !== field || !sortOrder) {
        return <ArrowUpDown className="w-4 h-4 text-gray-400" />;
      }
      return sortOrder === 'asc' ? (
        <ArrowUp className="w-4 h-4 text-blue-600" />
      ) : (
        <ArrowDown className="w-4 h-4 text-blue-600" />
      );
    },
    [sortField, sortOrder]
  );

  // 开始编辑单元格
  const startEdit = useCallback((rowId: string | number, field: string, currentValue: any) => {
    setEditingCell({ rowId, field });
    setEditValue(String(currentValue || ''));
  }, []);

  // 保存编辑
  const saveEdit = useCallback(() => {
    if (!editingCell) return;

    const item = items.find((i) => i.id === editingCell.rowId);
    if (item && onItemUpdate) {
      const updatedItem = {
        ...item,
        [editingCell.field]: editValue,
      };
      onItemUpdate(updatedItem);
    }

    setEditingCell(null);
    setEditValue('');
  }, [editingCell, editValue, items, onItemUpdate]);

  // 取消编辑
  const cancelEdit = useCallback(() => {
    setEditingCell(null);
    setEditValue('');
  }, []);

  // 切换选择
  const toggleSelect = useCallback((itemId: string | number) => {
    setSelectedItems((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  }, []);

  // 全选/取消全选
  const toggleSelectAll = useCallback(() => {
    if (selectedItems.size === filteredAndSortedItems.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(filteredAndSortedItems.map((item) => item.id)));
    }
  }, [selectedItems.size, filteredAndSortedItems]);

  // 批量删除
  const handleBatchDelete = useCallback(() => {
    if (selectedItems.size === 0 || !onBatchDelete) return;

    const itemsToDelete = filteredAndSortedItems.filter((item) => selectedItems.has(item.id));
    if (confirm(`确定要删除选中的 ${itemsToDelete.length} 项吗？`)) {
      onBatchDelete(itemsToDelete);
      setSelectedItems(new Set());
    }
  }, [selectedItems, filteredAndSortedItems, onBatchDelete]);

  // 导出数据
  const handleExport = useCallback(() => {
    const csvContent = [
      // 表头
      ['ID', '名称', '显示名称', '类型', '状态', '分类', '创建时间'].join(','),
      // 数据行
      ...filteredAndSortedItems.map((item) =>
        [
          item.id,
          item.name || '',
          item.display_name || '',
          item.type || item.asset_type || '',
          item.status || '',
          item.classification || '',
          item.created_at || '',
        ]
          .map((v) => `"${String(v).replace(/"/g, '""')}"`)
          .join(',')
      ),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `metadata_${type}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  }, [filteredAndSortedItems, type]);

  // 可编辑的字段
  const editableFields = ['display_name', 'description', 'status', 'classification'];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  if (filteredAndSortedItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <Info className="w-12 h-12 mb-4 text-gray-400" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-3">
        <div className="flex items-center gap-2">
          {/* 搜索 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm w-64"
            />
          </div>

          {/* 类型筛选 */}
          {allTypes.length > 0 && (
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="pl-10 pr-8 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white text-sm"
              >
                <option value="all">全部分类</option>
                {allTypes.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 批量操作 */}
          {editable && selectedItems.size > 0 && (
            <button
              onClick={handleBatchDelete}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              删除选中 ({selectedItems.size})
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            导出
          </button>
        </div>
      </div>

      {/* 表格 */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {editable && (
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={
                        selectedItems.size === filteredAndSortedItems.length &&
                        filteredAndSortedItems.length > 0
                      }
                      onChange={toggleSelectAll}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                )}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('name')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    名称
                    {getSortIcon('name')}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('display_name')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    显示名称
                    {getSortIcon('display_name')}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('type')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    类型
                    {getSortIcon('type')}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('status')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    状态
                    {getSortIcon('status')}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('created_at')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    创建时间
                    {getSortIcon('created_at')}
                  </button>
                </th>
                {editable && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedItems.map((item) => (
                <tr
                  key={item.id}
                  className={`hover:bg-gray-50 ${selectedItems.has(item.id) ? 'bg-blue-50' : ''}`}
                >
                  {editable && (
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedItems.has(item.id)}
                        onChange={() => toggleSelect(item.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                  )}
                  <td className="px-4 py-3 whitespace-nowrap">
                    {editingCell?.rowId === item.id && editingCell.field === 'name' ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit();
                            if (e.key === 'Escape') cancelEdit();
                          }}
                          className="px-2 py-1 border border-blue-500 rounded text-sm"
                          autoFocus
                        />
                        <button onClick={saveEdit} className="text-green-600 hover:text-green-700">
                          <Check className="w-4 h-4" />
                        </button>
                        <button onClick={cancelEdit} className="text-red-600 hover:text-red-700">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div
                        className="text-sm font-medium text-gray-900 cursor-pointer"
                        onClick={() =>
                          editable &&
                          editableFields.includes('name') &&
                          startEdit(item.id, 'name', item.name)
                        }
                      >
                        {item.name}
                        {editable && editableFields.includes('name') && (
                          <Edit2 className="w-3 h-3 inline-block ml-1 text-gray-400" />
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {editingCell?.rowId === item.id && editingCell.field === 'display_name' ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit();
                            if (e.key === 'Escape') cancelEdit();
                          }}
                          className="px-2 py-1 border border-blue-500 rounded text-sm w-full"
                          autoFocus
                        />
                        <button onClick={saveEdit} className="text-green-600 hover:text-green-700">
                          <Check className="w-4 h-4" />
                        </button>
                        <button onClick={cancelEdit} className="text-red-600 hover:text-red-700">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div
                        className="text-sm text-gray-900 cursor-pointer"
                        onClick={() =>
                          editable &&
                          editableFields.includes('display_name') &&
                          startEdit(item.id, 'display_name', item.display_name)
                        }
                      >
                        {item.display_name || '-'}
                        {editable && editableFields.includes('display_name') && (
                          <Edit2 className="w-3 h-3 inline-block ml-1 text-gray-400" />
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">
                      {item.type || item.asset_type || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {editingCell?.rowId === item.id && editingCell.field === 'status' ? (
                      <div className="flex items-center gap-2">
                        <select
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit();
                            if (e.key === 'Escape') cancelEdit();
                          }}
                          className="px-2 py-1 border border-blue-500 rounded text-sm"
                          autoFocus
                        >
                          <option value="active">active</option>
                          <option value="inactive">inactive</option>
                          <option value="pending">pending</option>
                        </select>
                        <button onClick={saveEdit} className="text-green-600 hover:text-green-700">
                          <Check className="w-4 h-4" />
                        </button>
                        <button onClick={cancelEdit} className="text-red-600 hover:text-red-700">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <span
                        className={`px-2 py-1 text-xs rounded cursor-pointer ${
                          item.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : item.status === 'inactive'
                              ? 'bg-gray-100 text-gray-800'
                              : 'bg-yellow-100 text-yellow-800'
                        }`}
                        onClick={() =>
                          editable &&
                          editableFields.includes('status') &&
                          startEdit(item.id, 'status', item.status)
                        }
                      >
                        {item.status || '-'}
                        {editable && editableFields.includes('status') && (
                          <Edit2 className="w-3 h-3 inline-block ml-1" />
                        )}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {item.created_at ? new Date(item.created_at).toLocaleDateString('zh-CN') : '-'}
                  </td>
                  {editable && (
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onItemClick?.(item)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          查看
                        </button>
                        {onItemDelete && (
                          <button
                            onClick={() => {
                              if (confirm('确定要删除此项吗？')) {
                                onItemDelete(item);
                              }
                            }}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
