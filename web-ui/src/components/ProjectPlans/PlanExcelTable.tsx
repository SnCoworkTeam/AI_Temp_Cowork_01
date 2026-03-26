'use client';

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import {
  Folder,
  FileText,
  Plus,
  Trash2,
  Lock,
  User,
  Calendar,
  Clock,
  GanttChart,
  ChevronRight,
  ChevronDown,
  Edit,
  AlertCircle,
} from 'lucide-react';
import { Button, Tag, Progress, Select, DatePicker, Tooltip } from 'antd';
import type { PlanTreeNode } from '@/types/project';
import dayjs from 'dayjs';
// react-data-grid样式 - 6.x版本可能不需要单独导入，或使用不同的路径

const { RangePicker } = DatePicker;

// 扩展的表格行类型
export interface PlanExcelRow extends PlanTreeNode {
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
  // 用于树形结构的字段
  _children?: PlanExcelRow[];
  _parent?: PlanExcelRow | null;
}

interface PlanExcelTableProps {
  tree: PlanTreeNode[];
  loading?: boolean;
  onAddTask?: (phaseId: string) => void;
  onEditTask?: (taskId: string) => void;
  onDeleteTask?: (taskId: string) => void;
  onUpdateTask?: (taskId: string, data: Partial<PlanExcelRow>) => void;
  onMoveTask?: (taskId: string, newParentId: string | null, newIndex: number) => void;
}

// 将树形结构转换为扁平化数组（保留层级信息）
function flattenTree(
  nodes: PlanTreeNode[],
  level: number = 0,
  parentId?: string,
  parent?: PlanExcelRow | null,
  expandedSet?: Set<string>
): PlanExcelRow[] {
  const result: PlanExcelRow[] = [];

  for (const node of nodes) {
    const isExpanded = expandedSet ? expandedSet.has(node.id) : level < 2;

    const row: PlanExcelRow = {
      ...node,
      level,
      parentId,
      expanded: isExpanded,
      phaseStatus:
        node.type === 'phase'
          ? node.status === 'completed'
            ? 'completed'
            : node.status === 'in_progress'
              ? 'active'
              : 'not-started'
          : undefined,
      taskStatus: node.type === 'task' ? (node.status as any) : undefined,
      priority:
        node.type === 'task'
          ? node.status === 'high'
            ? 'high'
            : node.status === 'medium'
              ? 'medium'
              : 'low'
          : undefined,
      _parent: parent,
      _children: node.children && node.children.length > 0 ? [] : undefined,
    };

    result.push(row);

    // 递归处理子节点（只有在展开时才添加）
    if (node.children && node.children.length > 0 && isExpanded) {
      const children = flattenTree(node.children, level + 1, node.id, row, expandedSet);
      result.push(...children);
      row._children = children;
    }
  }

  return result;
}

export default function PlanExcelTable({
  tree,
  loading = false,
  onAddTask,
  onEditTask,
  onDeleteTask,
  onUpdateTask,
  onMoveTask,
}: PlanExcelTableProps) {
  const [rows, setRows] = useState<PlanExcelRow[]>([]);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [editingCell, setEditingCell] = useState<{ rowId: string; columnKey: string } | null>(null);
  const [sortColumns, setSortColumns] = useState<readonly any[]>([]);
  const [DataGridComponent, setDataGridComponent] = useState<any>(null);
  const [dataGridLoading, setDataGridLoading] = useState(true);

  // 动态加载 DataGrid 组件
  // 注意：由于 react-data-grid 7.x 存在兼容性问题（Element type is invalid），已完全禁用
  // 当前使用列表视图作为替代方案
  useEffect(() => {
    // 直接禁用 react-data-grid，使用列表视图，避免渲染错误
    setDataGridComponent(null);
    setDataGridLoading(false);

    // 如果需要重新启用，需要解决 react-data-grid 7.x 的兼容性问题
    // 可能的解决方案：
    // 1. 降级到 react-data-grid 6.x（需要 React 16/17）
    // 2. 等待 react-data-grid 7.x 稳定版本
    // 3. 使用其他表格组件（如 ag-Grid、TanStack Table 等）
  }, []);

  // 初始化：将树形数据转换为扁平化数组
  useEffect(() => {
    if (tree && tree.length > 0) {
      // 默认展开所有阶段节点
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
      setExpandedRows(phaseIds);

      // 使用展开状态构建扁平化数组
      const flatRows = flattenTree(tree, 0, undefined, undefined, phaseIds);
      setRows(flatRows || []);
    } else {
      // 如果 tree 为空，确保 rows 也是空数组
      setRows([]);
    }
  }, [tree]);

  // 切换行展开/折叠
  const toggleRowExpand = useCallback(
    (rowId: string) => {
      setExpandedRows((prev) => {
        const next = new Set(prev);
        if (next.has(rowId)) {
          next.delete(rowId);
        } else {
          next.add(rowId);
        }
        // 重新构建行数据
        const flatRows = flattenTree(tree, 0, undefined, undefined, next);
        setRows(flatRows);
        return next;
      });
    },
    [tree]
  );

  // 计算阶段进度（基于子任务）
  const calculatePhaseProgress = useCallback((phaseId: string): number => {
    if (!rows || rows.length === 0) {
      return 0;
    }
    const phase = rows.find((r) => r.id === phaseId && r.type === 'phase');
    if (!phase || !phase._children || phase._children.length === 0) {
      return phase?.progress_percent || 0;
    }

    const tasks = phase._children.filter((child) => child.type === 'task');
    if (tasks.length === 0) {
      return 0;
    }

    const totalProgress = tasks.reduce((sum, task) => sum + (task.progress_percent || 0), 0);
    return Math.round(totalProgress / tasks.length);
  }, [rows]);

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

  // 处理行数据变更（兼容 6.x 和 7.x 版本）
  const handleRowsChange = useCallback(
    (newRows: any[], data?: any) => {
      const updatedRows = newRows as PlanExcelRow[];
      setRows(updatedRows);

      // 触发更新回调
      updatedRows.forEach((row) => {
        if (onUpdateTask && row.type === 'task') {
          onUpdateTask(row.id, {
            name: row.name,
            assignee: row.assignee,
            assigneeId: row.assigneeId,
            startDate: row.startDate,
            endDate: row.endDate,
            progress_percent: row.progress_percent,
            taskStatus: row.taskStatus,
            priority: row.priority,
            estimatedHours: row.estimatedHours,
          });
        }
      });
    },
    [onUpdateTask]
  );

  // 定义列
  const columns: any[] = useMemo(
    () => [
      {
        key: 'name',
        name: '名称',
        width: 350,
        resizable: true,
        sortable: true,
        frozen: true,
        renderCell: ({ row, onRowChange }: any) => {
          const isPhase = row.type === 'phase';
          const hasChildren = row._children && row._children.length > 0;
          const isExpanded = expandedRows.has(row.id);

          return (
            <div className="flex items-center gap-2" style={{ paddingLeft: `${row.level * 20}px` }}>
              {/* 展开/折叠图标 */}
              {hasChildren ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleRowExpand(row.id);
                  }}
                  className="flex items-center justify-center w-5 h-5 hover:bg-gray-200 rounded"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  )}
                </button>
              ) : (
                <span className="w-5" />
              )}

              {/* 图标 */}
              {isPhase ? (
                <Folder className="w-4 h-4 text-blue-500 flex-shrink-0" />
              ) : (
                <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
              )}

              {/* 名称（可编辑） */}
              {editingCell?.rowId === row.id && editingCell?.columnKey === 'name' ? (
                <input
                  type="text"
                  value={row.name}
                  onChange={(e) => {
                    onRowChange({ ...row, name: e.target.value });
                  }}
                  onBlur={() => setEditingCell(null)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      setEditingCell(null);
                    }
                  }}
                  autoFocus
                  className="flex-1 px-2 py-1 border border-blue-500 rounded"
                />
              ) : (
                <span
                  className={`flex-1 ${isPhase ? 'font-semibold text-gray-900' : 'text-gray-700'} cursor-pointer`}
                  onDoubleClick={() => {
                    if (!row.is_readonly) {
                      setEditingCell({ rowId: row.id, columnKey: 'name' });
                    }
                  }}
                >
                  {row.name}
                </span>
              )}

              {/* 只读标识 */}
              {row.is_readonly && (
                <Tooltip title="阶段节点，只读">
                  <Lock className="w-4 h-4 text-gray-400" />
                </Tooltip>
              )}

              {/* 阶段节点：添加任务按钮 */}
              {isPhase && onAddTask && (
                <Tooltip title="添加任务">
                  <Button
                    type="text"
                    size="small"
                    icon={<Plus className="w-4 h-4" />}
                    onClick={(e) => {
                      e.stopPropagation();
                      onAddTask?.(row.id);
                    }}
                    className="hover:bg-blue-100"
                  />
                </Tooltip>
              )}

              {/* 任务节点：删除按钮 */}
              {!isPhase && !row.is_readonly && onDeleteTask && (
                <Tooltip title="删除">
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('确定要删除这个任务吗？')) {
                        onDeleteTask?.(row.id);
                      }
                    }}
                    className="hover:bg-red-100"
                  />
                </Tooltip>
              )}
            </div>
          );
        },
      },
      {
        key: 'assignee',
        name: '负责人',
        width: 120,
        resizable: true,
        sortable: true,
        renderCell: ({ row, onRowChange }: any) => {
          if (row.type === 'phase') {
            return <span className="text-gray-400">-</span>;
          }

          if (editingCell?.rowId === row.id && editingCell?.columnKey === 'assignee') {
            return (
              <Select
                size="small"
                style={{ width: 100 }}
                value={row.assigneeId}
                onChange={(value) => {
                  onRowChange({ ...row, assigneeId: value });
                  setEditingCell(null);
                }}
                onBlur={() => setEditingCell(null)}
                open
              >
                {/* TODO: 从用户列表获取 */}
              </Select>
            );
          }

          return (
            <div
              className="flex items-center gap-1 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
              onDoubleClick={() => {
                setEditingCell({ rowId: row.id, columnKey: 'assignee' });
              }}
            >
              <User className="w-4 h-4 text-gray-400" />
              <span className="text-sm">{row.assignee || '未分配'}</span>
            </div>
          );
        },
      },
      {
        key: 'dateRange',
        name: '时间范围',
        width: 240,
        resizable: true,
        renderCell: ({ row, onRowChange }: any) => {
          if (row.type === 'phase') {
            return <span className="text-gray-400">-</span>;
          }

          if (editingCell?.rowId === row.id && editingCell?.columnKey === 'dateRange') {
            return (
              <RangePicker
                size="small"
                value={
                  row.startDate && row.endDate
                    ? [dayjs(row.startDate), dayjs(row.endDate)]
                    : null
                }
                onChange={(dates) => {
                  if (dates && dates[0] && dates[1]) {
                    onRowChange({
                      ...row,
                      startDate: dates[0].format('YYYY-MM-DD'),
                      endDate: dates[1].format('YYYY-MM-DD'),
                    });
                  }
                  setEditingCell(null);
                }}
                onBlur={() => setEditingCell(null)}
              />
            );
          }

          const startDate = row.startDate ? dayjs(row.startDate).format('YYYY-MM-DD') : '-';
          const endDate = row.endDate ? dayjs(row.endDate).format('YYYY-MM-DD') : '-';
          const duration =
            row.startDate && row.endDate
              ? dayjs(row.endDate).diff(dayjs(row.startDate), 'day') + 1
              : null;

          return (
            <div
              className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
              onDoubleClick={() => {
                setEditingCell({ rowId: row.id, columnKey: 'dateRange' });
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
        key: 'progress',
        name: '进度',
        width: 150,
        resizable: true,
        sortable: true,
        renderCell: ({ row, onRowChange }: any) => {
          const progress =
            row.type === 'phase' ? calculatePhaseProgress(row.id) : row.progress_percent || 0;

          if (editingCell?.rowId === row.id && editingCell?.columnKey === 'progress' && row.type === 'task') {
            return (
              <input
                type="number"
                min={0}
                max={100}
                value={progress}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onRowChange({ ...row, progress_percent: value });
                }}
                onBlur={() => setEditingCell(null)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    setEditingCell(null);
                  }
                }}
                autoFocus
                className="w-full px-2 py-1 border border-blue-500 rounded"
              />
            );
          }

          return (
            <div
              className="cursor-pointer"
              onDoubleClick={() => {
                if (row.type === 'task') {
                  setEditingCell({ rowId: row.id, columnKey: 'progress' });
                }
              }}
            >
              <Progress percent={progress} size="small" status={progress === 100 ? 'success' : 'active'} />
              <span className="text-xs text-gray-500 ml-2">{progress}%</span>
            </div>
          );
        },
      },
      {
        key: 'status',
        name: '状态',
        width: 120,
        resizable: true,
        sortable: true,
        renderCell: ({ row, onRowChange }: any) => {
          const status = row.type === 'phase' ? row.phaseStatus : row.taskStatus;
          const statusText =
            row.type === 'phase'
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

          if (editingCell?.rowId === row.id && editingCell?.columnKey === 'status') {
            return (
              <Select
                size="small"
                style={{ width: 100 }}
                value={status}
                onChange={(value) => {
                  if (row.type === 'phase') {
                    onRowChange({ ...row, phaseStatus: value });
                  } else {
                    onRowChange({ ...row, taskStatus: value });
                  }
                  setEditingCell(null);
                }}
                onBlur={() => setEditingCell(null)}
                open
              >
                {row.type === 'phase' ? (
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
              onDoubleClick={() => {
                setEditingCell({ rowId: row.id, columnKey: 'status' });
              }}
            >
              {statusText}
            </Tag>
          );
        },
      },
      {
        key: 'priority',
        name: '优先级',
        width: 100,
        resizable: true,
        sortable: true,
        renderCell: ({ row, onRowChange }: any) => {
          if (row.type === 'phase') {
            return <span className="text-gray-400">-</span>;
          }

          if (editingCell?.rowId === row.id && editingCell?.columnKey === 'priority') {
            return (
              <Select
                size="small"
                style={{ width: 80 }}
                value={row.priority}
                onChange={(value) => {
                  onRowChange({ ...row, priority: value });
                  setEditingCell(null);
                }}
                onBlur={() => setEditingCell(null)}
                open
              >
                <Select.Option value="low">低</Select.Option>
                <Select.Option value="medium">中</Select.Option>
                <Select.Option value="high">高</Select.Option>
              </Select>
            );
          }

          return (
            <Tag
              color={getPriorityColor(row.priority)}
              className="cursor-pointer"
              onDoubleClick={() => {
                setEditingCell({ rowId: row.id, columnKey: 'priority' });
              }}
            >
              {row.priority === 'high' ? '高' : row.priority === 'medium' ? '中' : '低'}
            </Tag>
          );
        },
      },
      {
        key: 'estimatedHours',
        name: '预估工时',
        width: 120,
        resizable: true,
        sortable: true,
        renderCell: ({ row, onRowChange }: any) => {
          if (row.type === 'phase') {
            return <span className="text-gray-400">-</span>;
          }

          if (editingCell?.rowId === row.id && editingCell?.columnKey === 'estimatedHours') {
            return (
              <input
                type="number"
                min={0}
                max={9999}
                value={row.estimatedHours || 0}
                onChange={(e) => {
                  const value = parseFloat(e.target.value) || 0;
                  onRowChange({ ...row, estimatedHours: value });
                }}
                onBlur={() => setEditingCell(null)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    setEditingCell(null);
                  }
                }}
                autoFocus
                className="w-full px-2 py-1 border border-blue-500 rounded"
              />
            );
          }

          return (
            <div
              className="flex items-center gap-1 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
              onDoubleClick={() => {
                setEditingCell({ rowId: row.id, columnKey: 'estimatedHours' });
              }}
            >
              <Clock className="w-4 h-4 text-gray-400" />
              <span className="text-sm">{row.estimatedHours || 0}h</span>
            </div>
          );
        },
      },
    ],
    [expandedRows, editingCell, calculatePhaseProgress, toggleRowExpand, onAddTask, onDeleteTask]
  );

  // 处理单元格点击
  const handleCellClick = useCallback((args: any) => {
    // 可以在这里添加点击逻辑
  }, []);

  // 处理键盘事件
  const handleCellKeyDown = useCallback((args: any) => {
    const { row, column, event } = args;

    // Tab键：移动到下一个单元格
    if (event.key === 'Tab') {
      event.preventDefault();
      // react-data-grid会自动处理Tab导航
    }

    // Enter键：进入编辑模式或移动到下一行
    if (event.key === 'Enter') {
      if (!row.is_readonly && column.key !== 'name') {
        setEditingCell({ rowId: row.id, columnKey: column.key });
      }
    }

    // F2键：进入编辑模式
    if (event.key === 'F2') {
      event.preventDefault();
      if (!row.is_readonly) {
        setEditingCell({ rowId: row.id, columnKey: column.key });
      }
    }

    // Delete键：删除任务
    if (event.key === 'Delete' && row.type === 'task' && !row.is_readonly && onDeleteTask) {
      if (confirm('确定要删除这个任务吗？')) {
        onDeleteTask(row.id);
      }
    }
  }, [onDeleteTask]);

  return (
    <div className="w-full">
      {/* 工具栏 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Button
            size="small"
            onClick={() => {
              const allIds = new Set<string>();
              const collectAllIds = (nodes: PlanTreeNode[]) => {
                for (const node of nodes) {
                  allIds.add(node.id);
                  if (node.children && node.children.length > 0) {
                    collectAllIds(node.children);
                  }
                }
              };
              collectAllIds(tree);

              const newExpanded = expandedRows.size === allIds.size ? new Set<string>() : allIds;
              setExpandedRows(newExpanded);
              // 重新构建行数据
              const flatRows = flattenTree(tree, 0, undefined, undefined, newExpanded);
              setRows(flatRows);
            }}
          >
            {expandedRows.size > 0 ? '全部折叠' : '全部展开'}
          </Button>
        </div>
        <div className="text-sm text-gray-500">
          提示：双击单元格进行编辑，使用Tab键切换单元格，Delete键删除任务
        </div>
      </div>

      {/* Excel 风格表格 */}
      <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
        {dataGridLoading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-3"></div>
            <p>加载表格组件...</p>
          </div>
        ) : !DataGridComponent ? (
          <div className="p-8 text-center">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-yellow-600" />
              <p className="text-yellow-800 font-medium mb-1">表格组件加载失败</p>
              <p className="text-sm text-yellow-700">
                react-data-grid 组件未正确加载，请检查依赖是否正确安装。
              </p>
            </div>
            {/* 降级到列表视图 */}
            <div className="overflow-auto" style={{ maxHeight: '600px' }}>
              {!rows || rows.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>暂无数据</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {rows.map((row) => {
                    const isPhase = row.type === 'phase';
                    const indentLevel = row.level || 0;
                    return (
                      <div
                        key={row.id}
                        className={`p-4 hover:bg-gray-50 transition-colors ${
                          isPhase ? 'bg-blue-50/50' : ''
                        }`}
                        style={{ paddingLeft: `${16 + indentLevel * 24}px` }}
                      >
                        <div className="flex items-center gap-2">
                          {isPhase ? (
                            <Folder className="w-5 h-5 text-blue-500" />
                          ) : (
                            <FileText className="w-4 h-4 text-gray-500" />
                          )}
                          <span className={`${isPhase ? 'font-semibold text-blue-700' : 'text-gray-900'}`}>
                            {row.name}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : dataGridLoading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-3"></div>
            <p>加载表格组件...</p>
          </div>
        ) : !DataGridComponent ? (
          <div className="p-8">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
              <div className="flex items-start gap-4">
                <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-yellow-900 font-semibold mb-2">表格组件暂时不可用</h3>
                  <p className="text-sm text-yellow-800 mb-3">
                    Excel 风格的表格组件加载失败，已自动切换到列表视图。您可以继续查看和编辑数据，但部分高级功能可能不可用。
                  </p>
                  <div className="text-xs text-yellow-700 space-y-1">
                    <p>• 数据查看和编辑功能正常</p>
                    <p>• 列表视图支持基本的展开/折叠功能</p>
                    <p>• 如需完整功能，请刷新页面重试</p>
                  </div>
                </div>
              </div>
            </div>
            {!rows || rows.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>暂无数据</p>
              </div>
            ) : (
              <div className="overflow-auto" style={{ maxHeight: '600px' }}>
                <div className="divide-y divide-gray-100">
                  {rows.map((row) => {
                    const isPhase = row.type === 'phase';
                    const indentLevel = row.level || 0;
                    return (
                      <div
                        key={row.id}
                        className={`p-4 hover:bg-gray-50 transition-colors ${
                          isPhase ? 'bg-blue-50/50' : ''
                        }`}
                        style={{ paddingLeft: `${16 + indentLevel * 24}px` }}
                      >
                        <div className="flex items-center gap-2">
                          {isPhase ? (
                            <Folder className="w-5 h-5 text-blue-500" />
                          ) : (
                            <FileText className="w-4 h-4 text-gray-500" />
                          )}
                          <span className={`${isPhase ? 'font-semibold text-blue-700' : 'text-gray-900'}`}>
                            {row.name}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ) : !rows || rows.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>暂无数据</p>
          </div>
        ) : !DataGridComponent ? (
          // DataGrid 组件未加载，使用列表视图
          <div className="overflow-auto" style={{ maxHeight: '600px' }}>
            <div className="divide-y divide-gray-100">
              {rows.map((row) => {
                const isPhase = row.type === 'phase';
                const indentLevel = row.level || 0;
                return (
                  <div
                    key={row.id}
                    className={`p-4 hover:bg-gray-50 transition-colors ${
                      isPhase ? 'bg-blue-50/50' : ''
                    }`}
                    style={{ paddingLeft: `${16 + indentLevel * 24}px` }}
                  >
                    <div className="flex items-center gap-2">
                      {isPhase ? (
                        <Folder className="w-5 h-5 text-blue-500" />
                      ) : (
                        <FileText className="w-4 h-4 text-gray-500" />
                      )}
                      <span className={`${isPhase ? 'font-semibold text-blue-700' : 'text-gray-900'}`}>
                        {row.name}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          (() => {
            try {
              // 确保 DataGridComponent 是一个有效的 React 组件
              if (!DataGridComponent) {
                throw new Error('DataGrid 组件未加载');
              }

              // 如果是函数，直接使用
              let Component = DataGridComponent;
              if (typeof DataGridComponent === 'object') {
                Component = (DataGridComponent as any).default || DataGridComponent;
              }

              if (!Component || typeof Component !== 'function') {
                throw new Error('DataGrid 组件不是有效的函数');
              }

              // 创建一个包装的 columns，确保 renderCell 正确处理参数
              const safeColumns = columns.map((col) => {
                if (col.renderCell) {
                  const originalRenderCell = col.renderCell;
                  return {
                    ...col,
                    renderCell: (props: any) => {
                      try {
                        // 确保 onRowChange 存在，如果不存在则使用 handleRowsChange
                        const safeProps = {
                          ...props,
                          onRowChange: props.onRowChange || ((newRow: any) => {
                            const updatedRows = rows.map((r) => (r.id === newRow.id ? newRow : r));
                            handleRowsChange(updatedRows);
                          }),
                        };
                        const result = originalRenderCell(safeProps);
                        // 确保返回值不是 undefined 或 null
                        if (result === undefined || result === null) {
                          console.warn('renderCell returned undefined/null for column:', col.key);
                          return <span className="text-gray-400">-</span>;
                        }
                        // 确保返回的是有效的 React 元素
                        if (typeof result === 'object' && '$$typeof' in result) {
                          return result;
                        }
                        // 如果不是 React 元素，包装成 span
                        return <span>{String(result)}</span>;
                      } catch (error) {
                        console.error('Error in renderCell:', error);
                        return <span className="text-red-500">渲染错误</span>;
                      }
                    },
                  };
                }
                // 移除可能不兼容的属性（frozen 在 7.x 中可能不支持）
                const { frozen, ...restCol } = col;
                return restCol;
              });

              // 验证 columns 是否有效
              if (!safeColumns || safeColumns.length === 0) {
                throw new Error('列配置无效');
              }

              // 移除可能不兼容的 props，只保留基本必需的 props
              const gridProps: any = {
                columns: safeColumns,
                rows: rows,
                onRowsChange: handleRowsChange,
                sortColumns: sortColumns,
                onSortColumnsChange: setSortColumns,
                defaultColumnOptions: {
                  resizable: true,
                  sortable: true,
                },
                style: { height: '600px', width: '100%' },
                className: 'rdg-light',
              };

              // 暂时注释掉可能不兼容的回调
              // if (handleCellClick) {
              //   gridProps.onCellClick = handleCellClick;
              // }
              // if (handleCellKeyDown) {
              //   gridProps.onCellKeyDown = handleCellKeyDown;
              // }

              return <Component {...gridProps} />;
            } catch (error: any) {
              console.error('DataGrid render error:', error);
              return (
                <div className="p-8">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                    <div className="flex items-start gap-4">
                      <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h3 className="text-red-900 font-semibold mb-2">表格渲染错误</h3>
                        <p className="text-sm text-red-800 mb-3">
                          表格组件在渲染时遇到错误。这可能是由于数据格式问题或组件版本不兼容导致的。
                        </p>
                        <p className="text-xs text-red-700">
                          错误信息: {error?.message || '未知错误'}
                        </p>
                      </div>
                    </div>
                  </div>
                  {/* 降级到列表视图 */}
                  {rows && rows.length > 0 ? (
                    <div className="mt-4 overflow-auto" style={{ maxHeight: '600px' }}>
                      <div className="divide-y divide-gray-100">
                        {rows.map((row) => {
                          const isPhase = row.type === 'phase';
                          const indentLevel = row.level || 0;
                          return (
                            <div
                              key={row.id}
                              className={`p-4 hover:bg-gray-50 transition-colors ${
                                isPhase ? 'bg-blue-50/50' : ''
                              }`}
                              style={{ paddingLeft: `${16 + indentLevel * 24}px` }}
                            >
                              <div className="flex items-center gap-2">
                                {isPhase ? (
                                  <Folder className="w-5 h-5 text-blue-500" />
                                ) : (
                                  <FileText className="w-4 h-4 text-gray-500" />
                                )}
                                <span className={`${isPhase ? 'font-semibold text-blue-700' : 'text-gray-900'}`}>
                                  {row.name}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-4 p-8 text-center text-gray-500">
                      <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                      <p>暂无数据</p>
                    </div>
                  )}
                </div>
              );
            }
          })()
        )}
      </div>
    </div>
  );
}

