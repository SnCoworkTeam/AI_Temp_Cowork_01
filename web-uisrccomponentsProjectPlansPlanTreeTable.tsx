'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FileText,
  Plus,
  Edit,
  Trash2,
  Lock,
  MoreVertical,
  Calendar,
  User,
  Clock,
  GanttChart,
} from 'lucide-react';
import { Table, Tag, Progress, Button, Input, DatePicker, Select, Tooltip, Dropdown, MenuProps } from 'antd';
import type { PlanTreeNode } from '@/types/project';
import dayjs, { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

// 扩展的树节点类型，包含表格所需的所有字段
export interface PlanTableItem extends PlanTreeNode {
  level: number;
  parentId?: string;
  expanded?: boolean;
  // 阶段特有字段
  phaseStatus?: 'not-started' | 'active' | 'completed';
  // 任务特有字段
  assignee?: string;
  assigneeId?: string;
  startDate?: string;
  endDate?: string;
  taskStatus?: 'todo' | 'in-progress' | 'review' | 'done';
  priority?: 'low' | 'medium' | 'high';
  estimatedHours?: number;
  actualHours?: number;
}

interface PlanTreeTableProps {
  tree: PlanTreeNode[];
  loading?: boolean;
  onAddTask?: (phaseId: string) => void;
  onEditTask?: (taskId: string) => void;
  onDeleteTask?: (taskId: string) => void;
  onUpdateTask?: (taskId: string, data: Partial<PlanTableItem>) => void;
  onMoveTask?: (taskId: string, newParentId: string | null, newIndex: number) => void;
}

// 将树形结构转换为扁平列表（用于表格展示）
function flattenTree(
  nodes: PlanTreeNode[],
  level: number = 0,
  parentId?: string,
  expandedNodes: Set<string> = new Set()
): PlanTableItem[] {
  const result: PlanTableItem[] = [];

  for (const node of nodes) {
    const isExpanded = expandedNodes.has(node.id);
    const item: PlanTableItem = {
      ...node,
      level,
      parentId,
      expanded: isExpanded,
      phaseStatus: node.type === 'phase' ? (node.status === 'completed' ? 'completed' : node.status === 'in_progress' ? 'active' : 'not-started') : undefined,
      taskStatus: node.type === 'task' ? (node.status as any) : undefined,
      priority: node.type === 'task' ? (node.status === 'high' ? 'high' : node.status === 'medium' ? 'medium' : 'low') : undefined,
    };

    result.push(item);

    // 如果节点展开且有子节点，递归处理
    if (isExpanded && node.children && node.children.length > 0) {
      result.push(...flattenTree(node.children, level + 1, node.id, expandedNodes));
    }
  }

  return result;
}

// 可拖拽的表格行组件
interface SortableTableRowProps {
  item: PlanTableItem;
  onToggleExpand: (id: string) => void;
  onAddTask?: (phaseId: string) => void;
  onEditTask?: (taskId: string) => void;
  onDeleteTask?: (taskId: string) => void;
  rowProps: any;
  isDragging: boolean;
}

function SortableTableRow({
  item,
  rowProps,
  isDragging,
}: SortableTableRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({
    id: item.id,
    disabled: item.is_readonly && item.type === 'phase', // 阶段节点不可拖拽
  });

  const style = {
    ...rowProps.style,
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const isPhase = item.type === 'phase';

  return (
    <tr
      {...rowProps}
      ref={setNodeRef}
      style={style}
      className={`group hover:bg-gray-50 ${isPhase ? 'bg-blue-50/50' : ''} ${isDragging ? 'shadow-lg' : ''} ${rowProps.className || ''}`}
    >
      {rowProps.children}
    </tr>
  );
}

export default function PlanTreeTable({
  tree,
  loading = false,
  onAddTask,
  onEditTask,
  onDeleteTask,
  onUpdateTask,
  onMoveTask,
}: PlanTreeTableProps) {
  // 默认展开所有阶段节点（type === 'phase'）
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(() => {
    const phaseIds = new Set<string>();
    const collectPhaseIds = (nodes: PlanTreeNode[]) => {
      for (const node of nodes) {
        if (node.type === 'phase') {
          phaseIds.add(node.id);
        }
        if (node.children && node.children.length > 0) {
          collectPhaseIds(node.children);
        }
      }
    };
    collectPhaseIds(tree);
    return phaseIds;
  });
  const [activeId, setActiveId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // 切换节点展开/折叠
  const toggleExpand = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  // 展开/折叠所有节点
  const toggleExpandAll = useCallback(() => {
    const allNodeIds = new Set<string>();
    const collectIds = (nodes: PlanTreeNode[]) => {
      for (const node of nodes) {
        allNodeIds.add(node.id);
        if (node.children) {
          collectIds(node.children);
        }
      }
    };
    collectIds(tree);

    if (expandedNodes.size === allNodeIds.size) {
      setExpandedNodes(new Set());
    } else {
      setExpandedNodes(allNodeIds);
    }
  }, [tree, expandedNodes]);

  // 扁平化树形结构
  const flatData = useMemo(() => {
    return flattenTree(tree, 0, undefined, expandedNodes);
  }, [tree, expandedNodes]);

  // 当树结构变化时，自动展开所有阶段节点
  useEffect(() => {
    const phaseIds = new Set<string>();
    const collectPhaseIds = (nodes: PlanTreeNode[]) => {
      for (const node of nodes) {
        if (node.type === 'phase') {
          phaseIds.add(node.id);
        }
        if (node.children && node.children.length > 0) {
          collectPhaseIds(node.children);
        }
      }
    };
    collectPhaseIds(tree);
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      phaseIds.forEach((id) => next.add(id));
      return next;
    });
  }, [tree]);

  // 拖拽开始
  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  // 拖拽结束
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over || active.id === over.id) {
      return;
    }

    const activeItem = flatData.find((item) => item.id === active.id);
    const overItem = flatData.find((item) => item.id === over.id);

    if (!activeItem || !overItem || activeItem.is_readonly) {
      return;
    }

    // 不能将任务拖到任务下（只能拖到阶段下）
    if (activeItem.type === 'task' && overItem.type === 'task') {
      return;
    }

    // 计算新位置
    const oldIndex = flatData.findIndex((item) => item.id === active.id);
    const newIndex = flatData.findIndex((item) => item.id === over.id);

    // 确定新的父节点ID
    let newParentId: string | null = null;
    if (overItem.type === 'phase') {
      newParentId = overItem.id;
    } else if (overItem.parentId) {
      newParentId = overItem.parentId;
    }

    // 调用移动回调
    if (onMoveTask) {
      onMoveTask(activeItem.id, newParentId, newIndex);
    }
  };

  // 获取状态标签颜色
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
      case 'done':
        return 'green';
      case 'in_progress':
      case 'active':
        return 'blue';
      case 'review':
        return 'orange';
      case 'todo':
      case 'not-started':
        return 'default';
      default:
        return 'default';
    }
  };

  // 获取优先级颜色
  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high':
        return 'red';
      case 'medium':
        return 'orange';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  // 计算阶段进度（基于子任务）
  const calculatePhaseProgress = (phaseId: string): number => {
    const phase = tree.find((node) => node.id === phaseId);
    if (!phase || !phase.children || phase.children.length === 0) {
      return phase?.progress_percent || 0;
    }

    const tasks = phase.children.filter((child) => child.type === 'task');
    if (tasks.length === 0) {
      return 0;
    }

    const totalProgress = tasks.reduce((sum, task) => sum + (task.progress_percent || 0), 0);
    return Math.round(totalProgress / tasks.length);
  };

  const columns = [
    {
      title: '名称',
      key: 'name',
      width: 300,
      render: (_: any, record: PlanTableItem) => {
        const isPhase = record.type === 'phase';
        const hasChildren = record.children && record.children.length > 0;

        return (
          <div className="flex items-center gap-2" style={{ paddingLeft: `${record.level * 24}px` }}>
            {hasChildren ? (
              <button
                onClick={() => toggleExpand(record.id)}
                className="flex items-center justify-center w-5 h-5 hover:bg-gray-200 rounded"
              >
                {record.expanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                )}
              </button>
            ) : (
              <div className="w-5" />
            )}

            {isPhase ? (
              <Folder className="w-4 h-4 text-blue-500 flex-shrink-0" />
            ) : (
              <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
            )}

            <span className={`flex-1 ${isPhase ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
              {record.name}
            </span>

            {record.is_readonly && (
              <Tooltip title="阶段节点，只读">
                <Lock className="w-4 h-4 text-gray-400" />
              </Tooltip>
            )}

            {/* 阶段节点：显示添加任务按钮（即使is_readonly） */}
            {isPhase && onAddTask && (
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Tooltip title="添加任务">
                  <Button
                    type="text"
                    size="small"
                    icon={<Plus className="w-4 h-4" />}
                    onClick={() => onAddTask?.(record.id)}
                  />
                </Tooltip>
              </div>
            )}

            {/* 任务节点：显示编辑和删除按钮 */}
            {!isPhase && !record.is_readonly && (
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {onEditTask && (
                  <Tooltip title="编辑">
                    <Button
                      type="text"
                      size="small"
                      icon={<Edit className="w-4 h-4" />}
                      onClick={() => onEditTask?.(record.id)}
                    />
                  </Tooltip>
                )}
                {onDeleteTask && (
                  <Tooltip title="删除">
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<Trash2 className="w-4 h-4" />}
                      onClick={() => onDeleteTask?.(record.id)}
                    />
                  </Tooltip>
                )}
              </div>
            )}

            {!record.is_readonly && (
              <div
                className="cursor-move p-1 hover:bg-gray-200 rounded"
                title="拖拽排序"
              >
                <GanttChart className="w-4 h-4 text-gray-400" />
              </div>
            )}
          </div>
        );
      },
    },
    {
      title: '负责人',
      key: 'assignee',
      width: 120,
      render: (_: any, record: PlanTableItem) => {
        if (record.type === 'phase') {
          return <span className="text-gray-400">-</span>;
        }

        if (editingId === record.id && editingField === 'assignee') {
          return (
            <Select
              size="small"
              style={{ width: 100 }}
              value={record.assigneeId}
              onChange={(value) => {
                onUpdateTask?.(record.id, { assigneeId: value });
                setEditingId(null);
                setEditingField(null);
              }}
              onBlur={() => {
                setEditingId(null);
                setEditingField(null);
              }}
            >
              {/* TODO: 从用户列表获取 */}
            </Select>
          );
        }

        return (
          <div
            className="flex items-center gap-1 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
            onClick={() => {
              setEditingId(record.id);
              setEditingField('assignee');
            }}
          >
            <User className="w-4 h-4 text-gray-400" />
            <span className="text-sm">{record.assignee || '未分配'}</span>
          </div>
        );
      },
    },
    {
      title: '时间范围',
      key: 'dateRange',
      width: 240,
      render: (_: any, record: PlanTableItem) => {
        if (record.type === 'phase') {
          return <span className="text-gray-400">-</span>;
        }

        if (editingId === record.id && editingField === 'dateRange') {
          return (
            <RangePicker
              size="small"
              value={
                record.startDate && record.endDate
                  ? [dayjs(record.startDate), dayjs(record.endDate)]
                  : null
              }
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  onUpdateTask?.(record.id, {
                    startDate: dates[0].format('YYYY-MM-DD'),
                    endDate: dates[1].format('YYYY-MM-DD'),
                  });
                }
                setEditingId(null);
                setEditingField(null);
              }}
              onBlur={() => {
                setEditingId(null);
                setEditingField(null);
              }}
            />
          );
        }

        const startDate = record.startDate ? dayjs(record.startDate).format('YYYY-MM-DD') : '-';
        const endDate = record.endDate ? dayjs(record.endDate).format('YYYY-MM-DD') : '-';
        const duration =
          record.startDate && record.endDate
            ? dayjs(record.endDate).diff(dayjs(record.startDate), 'day') + 1
            : null;

        return (
          <div
            className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
            onClick={() => {
              setEditingId(record.id);
              setEditingField('dateRange');
            }}
          >
            <Calendar className="w-4 h-4 text-gray-400" />
            <div className="text-sm">
              <div>{startDate} ~ {endDate}</div>
              {duration && <div className="text-xs text-gray-500">{duration} 天</div>}
            </div>
          </div>
        );
      },
    },
    {
      title: '进度',
      key: 'progress',
      width: 150,
      render: (_: any, record: PlanTableItem) => {
        const progress = record.type === 'phase'
          ? calculatePhaseProgress(record.id)
          : (record.progress_percent || 0);

        if (editingId === record.id && editingField === 'progress' && record.type === 'task') {
          return (
            <Input
              type="number"
              size="small"
              min={0}
              max={100}
              value={progress}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                onUpdateTask?.(record.id, { progress_percent: value });
              }}
              onBlur={() => {
                setEditingId(null);
                setEditingField(null);
              }}
              suffix="%"
            />
          );
        }

        return (
          <div
            className="cursor-pointer"
            onClick={() => {
              if (record.type === 'task') {
                setEditingId(record.id);
                setEditingField('progress');
              }
            }}
          >
            <Progress
              percent={progress}
              size="small"
              status={progress === 100 ? 'success' : 'active'}
            />
            <span className="text-xs text-gray-500 ml-2">{progress}%</span>
          </div>
        );
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 120,
      render: (_: any, record: PlanTableItem) => {
        const status = record.type === 'phase' ? record.phaseStatus : record.taskStatus;
        const statusText =
          record.type === 'phase'
            ? status === 'completed'
              ? '已完成'
              : status === 'active'
                ? '进行中'
                : '未开始'
            : status === 'done'
              ? '已完成'
              : status === 'in-progress'
                ? '进行中'
                : status === 'review'
                  ? '评审中'
                  : '待办';

        if (editingId === record.id && editingField === 'status') {
          return (
            <Select
              size="small"
              style={{ width: 100 }}
              value={status}
              onChange={(value) => {
                if (record.type === 'phase') {
                  onUpdateTask?.(record.id, { phaseStatus: value });
                } else {
                  onUpdateTask?.(record.id, { taskStatus: value });
                }
                setEditingId(null);
                setEditingField(null);
              }}
              onBlur={() => {
                setEditingId(null);
                setEditingField(null);
              }}
            >
              {record.type === 'phase' ? (
                <>
                  <Select.Option value="not-started">未开始</Select.Option>
                  <Select.Option value="active">进行中</Select.Option>
                  <Select.Option value="completed">已完成</Select.Option>
                </>
              ) : (
                <>
                  <Select.Option value="todo">待办</Select.Option>
                  <Select.Option value="in-progress">进行中</Select.Option>
                  <Select.Option value="review">评审中</Select.Option>
                  <Select.Option value="done">已完成</Select.Option>
                </>
              )}
            </Select>
          );
        }

        return (
          <Tag
            color={getStatusColor(status)}
            className="cursor-pointer"
            onClick={() => {
              setEditingId(record.id);
              setEditingField('status');
            }}
          >
            {statusText}
          </Tag>
        );
      },
    },
    {
      title: '优先级',
      key: 'priority',
      width: 100,
      render: (_: any, record: PlanTableItem) => {
        if (record.type === 'phase') {
          return <span className="text-gray-400">-</span>;
        }

        if (editingId === record.id && editingField === 'priority') {
          return (
            <Select
              size="small"
              style={{ width: 80 }}
              value={record.priority}
              onChange={(value) => {
                onUpdateTask?.(record.id, { priority: value });
                setEditingId(null);
                setEditingField(null);
              }}
              onBlur={() => {
                setEditingId(null);
                setEditingField(null);
              }}
            >
              <Select.Option value="low">低</Select.Option>
              <Select.Option value="medium">中</Select.Option>
              <Select.Option value="high">高</Select.Option>
            </Select>
          );
        }

        return (
          <Tag
            color={getPriorityColor(record.priority)}
            className="cursor-pointer"
            onClick={() => {
              setEditingId(record.id);
              setEditingField('priority');
            }}
          >
            {record.priority === 'high' ? '高' : record.priority === 'medium' ? '中' : '低'}
          </Tag>
        );
      },
    },
    {
      title: '预估工时',
      key: 'estimatedHours',
      width: 120,
      render: (_: any, record: PlanTableItem) => {
        if (record.type === 'phase') {
          return <span className="text-gray-400">-</span>;
        }

        if (editingId === record.id && editingField === 'estimatedHours') {
          return (
            <Input
              type="number"
              size="small"
              min={0}
              value={record.estimatedHours || 0}
              onChange={(e) => {
                const value = parseFloat(e.target.value) || 0;
                onUpdateTask?.(record.id, { estimatedHours: value });
              }}
              onBlur={() => {
                setEditingId(null);
                setEditingField(null);
              }}
              suffix="h"
            />
          );
        }

        return (
          <div
            className="flex items-center gap-1 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
            onClick={() => {
              setEditingId(record.id);
              setEditingField('estimatedHours');
            }}
          >
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-sm">{record.estimatedHours || 0}h</span>
          </div>
        );
      },
    },
  ];

  return (
    <div className="w-full">
      {/* 工具栏 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Button size="small" onClick={toggleExpandAll}>
            {expandedNodes.size > 0 ? '全部折叠' : '全部展开'}
          </Button>
        </div>
      </div>

      {/* 表格 */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={flatData.map((item) => item.id)} strategy={verticalListSortingStrategy}>
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <Table
              dataSource={flatData}
              columns={columns}
              rowKey="id"
              pagination={false}
              loading={loading}
              size="small"
              className="plan-tree-table"
            />
          </div>
        </SortableContext>

        <DragOverlay>
          {activeId ? (
            <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
              {flatData.find((item) => item.id === activeId)?.name}
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}


