'use client';

import React from 'react';
import {
  Database,
  FileText,
  Workflow,
  Bot,
  Building2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  MoreVertical,
  Eye,
  Edit,
  Link as LinkIcon,
} from 'lucide-react';
import { getClassificationDisplayName } from '@/lib/metadata-classification';

type MetadataType = 'data-assets' | 'workflows' | 'ai-models' | 'business-entities' | 'all';

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

interface MetadataCardProps {
  item: MetadataItem;
  type: 'data-assets' | 'workflows' | 'ai-models' | 'business-entities' | 'all';
  onClick?: (item: MetadataItem) => void;
  compact?: boolean;
}

// 类型图标映射
const getTypeIcon = (type: string) => {
  const iconMap: Record<string, React.ReactNode> = {
    'data-assets': <Database className="w-5 h-5" />,
    workflows: <Workflow className="w-5 h-5" />,
    'ai-models': <Bot className="w-5 h-5" />,
    'business-entities': <Building2 className="w-5 h-5" />,
    default: <FileText className="w-5 h-5" />,
  };
  return iconMap[type] || iconMap['default'];
};

// 状态图标映射
const getStatusIcon = (status?: string) => {
  if (!status) return null;

  const statusMap: Record<string, React.ReactNode> = {
    active: <CheckCircle2 className="w-4 h-4 text-green-600" />,
    inactive: <XCircle className="w-4 h-4 text-gray-400" />,
    deprecated: <AlertCircle className="w-4 h-4 text-yellow-600" />,
    archived: <AlertCircle className="w-4 h-4 text-gray-500" />,
  };
  return statusMap[status.toLowerCase()] || null;
};

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

// 截断文本
const truncate = (text: string, maxLength: number) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export function MetadataCard({ item, type, onClick, compact = false }: MetadataCardProps) {
  const handleClick = () => {
    onClick?.(item);
  };

  // 动态内容区域 - 根据类型显示不同内容
  const renderDynamicContent = () => {
    if (compact) return null;

    switch (type) {
      case 'data-assets':
        // 数据资产：显示数据预览或统计信息
        if (item.metadata?.record_count !== undefined) {
          return (
            <div className="text-xs text-gray-500 space-y-1">
              <div>记录数: {item.metadata.record_count.toLocaleString()}</div>
              {item.metadata.size_bytes && (
                <div>大小: {(item.metadata.size_bytes / 1024).toFixed(2)} KB</div>
              )}
            </div>
          );
        }
        break;

      case 'ai-models':
        // AI模型：显示性能指标
        if (item.metadata?.accuracy !== undefined) {
          return (
            <div className="text-xs text-gray-500">
              准确率: {(item.metadata.accuracy * 100).toFixed(1)}%
            </div>
          );
        }
        break;

      case 'workflows':
        // 工作流：显示执行统计
        if (item.metadata?.execution_count !== undefined) {
          return (
            <div className="text-xs text-gray-500">执行次数: {item.metadata.execution_count}</div>
          );
        }
        break;

      default:
        break;
    }
    return null;
  };

  return (
    <div
      className={`
        bg-white rounded-lg border border-gray-200 p-4 
        hover:shadow-md transition-all duration-200 cursor-pointer
        ${compact ? 'p-3' : ''}
      `}
      onClick={handleClick}
    >
      {/* 卡片头部 */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {/* 类型图标 */}
          <div className="flex-shrink-0 mt-1 text-gray-400">{getTypeIcon(type)}</div>

          {/* 标题区域 */}
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-gray-900 mb-1 truncate">
              {item.display_name || item.name}
            </h3>
            {item.name && item.name !== item.display_name && (
              <p className="text-xs text-gray-500 truncate">{item.name}</p>
            )}
          </div>
        </div>

        {/* 状态和操作 */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {item.status && (
            <div className="flex items-center gap-1">
              {getStatusIcon(item.status)}
              <span className="text-xs text-gray-500">{item.status}</span>
            </div>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              // TODO: 显示更多操作菜单
            }}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <MoreVertical className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* 描述 */}
      {item.description && !compact && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{truncate(item.description, 100)}</p>
      )}

      {/* 动态内容区域 */}
      {!compact && <div className="mb-3">{renderDynamicContent()}</div>}

      {/* 标签和分类 */}
      <div className="flex flex-wrap gap-2 mb-2">
        {item.classification && (
          <span className="px-2 py-1 text-xs rounded bg-blue-50 text-blue-700 border border-blue-200">
            {getClassificationDisplayName(item.classification, type)}
          </span>
        )}
        {item.asset_type && (
          <span className="px-2 py-1 text-xs rounded bg-gray-50 text-gray-700 border border-gray-200">
            {item.asset_type}
          </span>
        )}
        {item.tags && item.tags.length > 0 && (
          <>
            {item.tags.slice(0, 2).map((tag, idx) => (
              <span
                key={idx}
                className="px-2 py-1 text-xs rounded bg-gray-50 text-gray-600 border border-gray-200"
              >
                {tag}
              </span>
            ))}
            {item.tags.length > 2 && (
              <span className="px-2 py-1 text-xs text-gray-500">+{item.tags.length - 2}</span>
            )}
          </>
        )}
      </div>

      {/* 卡片底部 */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
        <div className="flex items-center gap-3">
          {item.created_at && <span>{formatDate(item.created_at)}</span>}
          {item.metadata?.owner && <span>所有者: {item.metadata.owner}</span>}
        </div>

        {/* 快速操作按钮 */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClick?.(item);
            }}
            className="p-1 hover:bg-gray-100 rounded"
            title="查看详情"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
