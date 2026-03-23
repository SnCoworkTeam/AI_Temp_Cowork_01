'use client';

import { useState, useMemo } from 'react';
import { Card, Button, Spin, Empty, Tag, Tooltip } from 'antd';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FileText,
  Plus,
  Edit,
  Trash2,
  Lock,
} from 'lucide-react';
import type { PlanTreeNode } from '@/types/project';

interface PlanTreeViewProps {
  tree: PlanTreeNode[];
  loading?: boolean;
  selectedNodeId?: string;
  onAddTask?: (parentId: string, parentType: 'phase' | 'task') => void;
  onEditTask?: (taskId: string) => void;
  onDeleteTask?: (taskId: string) => void;
  onNodeSelect?: (nodeId: string, nodeType: 'phase' | 'task') => void;
}

interface TreeNodeProps {
  node: PlanTreeNode;
  level: number;
  selectedNodeId?: string;
  onAddTask?: (parentId: string, parentType: 'phase' | 'task') => void;
  onEditTask?: (taskId: string) => void;
  onDeleteTask?: (taskId: string) => void;
  onNodeSelect?: (nodeId: string, nodeType: 'phase' | 'task') => void;
}

function TreeNode({
  node,
  level,
  selectedNodeId,
  onAddTask,
  onEditTask,
  onDeleteTask,
  onNodeSelect,
}: TreeNodeProps) {
  const [expanded, setExpanded] = useState(level < 2); // 默认展开前两级

  const hasChildren = node.children && node.children.length > 0;
  const isPhase = node.type === 'phase';
  const isReadonly = node.is_readonly;
  const isSelected = selectedNodeId === node.id;

  const handleToggle = () => {
    if (hasChildren) {
      setExpanded(!expanded);
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'in_progress':
        return 'blue';
      case 'pending':
        return 'orange';
      default:
        return 'default';
    }
  };

  return (
    <div className="select-none">
      <div
        className={`group flex items-center gap-2 py-2 px-3 rounded hover:bg-gray-50 cursor-pointer transition-colors ${
          isPhase ? 'bg-blue-50' : ''
        } ${isSelected ? 'bg-blue-100 border-l-4 border-blue-500' : ''}`}
        style={{ paddingLeft: `${level * 24 + 12}px` }}
        onClick={() => onNodeSelect?.(node.id, node.type)}
      >
        {hasChildren && (
          <button
            onClick={handleToggle}
            className="flex items-center justify-center w-5 h-5 hover:bg-gray-200 rounded"
          >
            {expanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        )}
        {!hasChildren && <div className="w-5" />}

        <div className="flex items-center gap-2 flex-1 min-w-0">
          {isPhase ? (
            <Folder className="w-4 h-4 text-blue-500 flex-shrink-0" />
          ) : (
            <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
          )}

          <span
            className={`flex-1 truncate ${
              isReadonly ? 'text-gray-600' : 'text-gray-900'
            }`}
          >
            {node.name}
          </span>

          {isReadonly && (
            <Tooltip title="阶段节点，只读">
              <Lock className="w-4 h-4 text-gray-400" />
            </Tooltip>
          )}

          {node.sequence !== undefined && (
            <Tag color="blue" className="text-xs">
              {node.sequence}
            </Tag>
          )}

          {node.status && (
            <Tag color={getStatusColor(node.status)} className="text-xs">
              {node.status}
            </Tag>
          )}

          {node.progress_percent !== undefined && (
            <span className="text-xs text-gray-500">
              {node.progress_percent}%
            </span>
          )}
        </div>

        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {onAddTask && (
            <Tooltip title={isPhase ? '添加任务' : '添加子任务'}>
              <Button
                type="text"
                size="small"
                icon={<Plus className="w-4 h-4" />}
                onClick={() => onAddTask(node.id, node.type)}
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              />
            </Tooltip>
          )}
          {!isPhase && onEditTask && (
            <Tooltip title="编辑任务">
              <Button
                type="text"
                size="small"
                icon={<Edit className="w-4 h-4" />}
                onClick={() => onEditTask(node.id)}
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              />
            </Tooltip>
          )}
          {!isPhase && onDeleteTask && (
            <Tooltip title="删除任务">
              <Button
                type="text"
                size="small"
                danger
                icon={<Trash2 className="w-4 h-4" />}
                onClick={() => onDeleteTask(node.id)}
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              />
            </Tooltip>
          )}
        </div>
      </div>

      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedNodeId={selectedNodeId}
              onAddTask={onAddTask}
              onEditTask={onEditTask}
              onDeleteTask={onDeleteTask}
              onNodeSelect={onNodeSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function PlanTreeView({
  tree,
  loading = false,
  selectedNodeId,
  onAddTask,
  onEditTask,
  onDeleteTask,
  onNodeSelect,
}: PlanTreeViewProps) {
  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spin size="large" />
      </div>
    );
  }

  if (tree.length === 0) {
    return (
      <div className="flex justify-center py-8">
        <Empty description="暂无计划数据" />
      </div>
    );
  }

  return (
      <div className="h-full flex flex-col">
      <div className="mb-4 pb-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Folder className="w-5 h-5 text-indigo-500" />
            <h3 className="text-lg font-bold text-gray-900">计划树形结构</h3>
          </div>
          {onAddTask && (
            <button
              onClick={() => {
                // 如果有根节点，在根节点下添加
                if (tree.length > 0 && tree[0].type === 'phase') {
                  onAddTask(tree[0].id, 'phase');
                }
              }}
              className="px-3 py-1.5 bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-sm rounded-lg hover:from-indigo-600 hover:to-purple-600 transition-all shadow-sm hover:shadow-md flex items-center gap-1"
              title="添加根任务"
            >
              <Plus className="w-4 h-4" />
              <span>添加</span>
            </button>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-auto">
        {tree.map((node) => (
          <TreeNode
            key={node.id}
            node={node}
            level={0}
            selectedNodeId={selectedNodeId}
            onAddTask={onAddTask}
            onEditTask={onEditTask}
            onDeleteTask={onDeleteTask}
            onNodeSelect={onNodeSelect}
          />
        ))}
      </div>
    </div>
  );
}

