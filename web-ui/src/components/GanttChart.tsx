'use client';

import { useEffect, useRef, useState } from 'react';
// @ts-ignore - frappe-gantt 可能没有类型定义
// frappe-gantt 的默认导出是 Gantt 类
import Gantt from 'frappe-gantt';

interface GanttTask {
  id: string;
  name: string;
  start: string;
  end: string;
  progress: number;
  dependencies?: string;
  custom_class?: string;
  is_critical?: boolean;
}

interface GanttChartProps {
  tasks: GanttTask[];
  onTaskChange?: (taskId: string, start: Date, end: Date) => void;
  onTaskClick?: (taskId: string) => void;
  viewMode?: 'Quarter Day' | 'Half Day' | 'Day' | 'Week' | 'Month';
  height?: number;
}

export default function GanttChart({
  tasks,
  onTaskChange,
  onTaskClick,
  viewMode = 'Month',
  height = 600,
}: GanttChartProps) {
  const ganttRef = useRef<HTMLDivElement>(null);
  const ganttInstanceRef = useRef<Gantt | null>(null);
  const [currentViewMode, setCurrentViewMode] = useState(viewMode);

  useEffect(() => {
    if (!ganttRef.current || !tasks || tasks.length === 0) return;

    // 转换任务数据格式
    const ganttTasks = tasks.map((task) => ({
      id: task.id,
      name: task.name,
      start: task.start,
      end: task.end,
      progress: task.progress || 0,
      dependencies: task.dependencies || '',
      custom_class: task.is_critical ? 'critical-task' : task.custom_class || '',
    }));

    try {
      // 销毁旧实例
      if (ganttInstanceRef.current) {
        // Frappe Gantt 没有直接的销毁方法，需要清空容器
        ganttRef.current.innerHTML = '';
      }

      // 创建新的 Gantt 实例
      const gantt = new Gantt(ganttRef.current, ganttTasks, {
        view_mode: currentViewMode as any,
        header_height: 50,
        column_width: 30,
        step: 24,
        bar_height: 20,
        bar_corner_radius: 3,
        arrow_curve: 5,
        padding: 18,
        date_format: 'YYYY-MM-DD',
        language: 'zh',
        on_click: (task: any) => {
          onTaskClick?.(task.id);
        },
        on_date_change: (task: any, start: Date, end: Date) => {
          onTaskChange?.(task.id, start, end);
        },
        on_progress_change: (task: any, progress: number) => {
          // 进度变更处理
          console.log('Progress changed:', task.id, progress);
        },
        on_view_change: (mode: string) => {
          setCurrentViewMode(mode);
        },
      });

      ganttInstanceRef.current = gantt;

      // 添加关键路径样式
      if (typeof document !== 'undefined') {
        const style = document.createElement('style');
        style.textContent = `
          .critical-task .bar-progress {
            fill: #ef4444 !important;
          }
          .critical-task .bar {
            fill: #dc2626 !important;
          }
        `;
        if (!document.head.querySelector('#gantt-critical-style')) {
          style.id = 'gantt-critical-style';
          document.head.appendChild(style);
        }
      }
    } catch (error) {
      console.error('Gantt chart initialization error:', error);
    }

    return () => {
      // 清理
      if (ganttRef.current) {
        ganttRef.current.innerHTML = '';
      }
    };
  }, [tasks, currentViewMode, onTaskChange, onTaskClick]);

  const changeViewMode = (mode: string) => {
    if (ganttInstanceRef.current) {
      ganttInstanceRef.current.change_view_mode(mode as any);
      setCurrentViewMode(mode);
    }
  };

  return (
    <div className="gantt-chart-container">
      {/* 视图模式切换按钮 */}
      <div className="flex items-center gap-2 mb-4 p-2 bg-gray-50 rounded-lg">
        <span className="text-sm font-medium text-gray-700">视图模式：</span>
        <div className="flex gap-1">
          {['Quarter Day', 'Half Day', 'Day', 'Week', 'Month'].map((mode) => (
            <button
              key={mode}
              onClick={() => changeViewMode(mode)}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                currentViewMode === mode
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {mode === 'Quarter Day'
                ? '1/4天'
                : mode === 'Half Day'
                  ? '半天'
                  : mode === 'Day'
                    ? '天'
                    : mode === 'Week'
                      ? '周'
                      : '月'}
            </button>
          ))}
        </div>
      </div>

      {/* 图例 */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500 rounded"></div>
          <span className="text-gray-600">普通任务</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-600 rounded"></div>
          <span className="text-gray-600">关键任务</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 rounded"></div>
          <span className="text-gray-600">依赖关系</span>
        </div>
      </div>

      {/* Gantt 图表容器 */}
      <div
        ref={ganttRef}
        className="gantt-container border border-gray-200 rounded-lg overflow-auto"
        style={{ height: `${height}px` }}
      />
    </div>
  );
}
