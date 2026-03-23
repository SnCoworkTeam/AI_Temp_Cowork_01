'use client';

import React from 'react';

interface GanttTask {
  id: string;
  name: string;
  start: Date;
  end: Date;
  progress: number;
  status: string;
  type: 'project' | 'phase' | 'task' | 'milestone';
}

interface GanttChartProps {
  tasks: GanttTask[];
  startDate?: Date;
  endDate?: Date;
  height?: number;
}

export const GanttChart: React.FC<GanttChartProps> = ({
  tasks,
  startDate,
  endDate,
  height = 400,
}) => {
  if (!tasks || tasks.length === 0) {
    return <div className="flex items-center justify-center h-64 text-gray-500">暂无数据</div>;
  }

  // 计算日期范围
  const allDates = tasks.flatMap((t) => [t.start, t.end]);
  const minDate = startDate || new Date(Math.min(...allDates.map((d) => d.getTime())));
  const maxDate = endDate || new Date(Math.max(...allDates.map((d) => d.getTime())));
  const totalDays = Math.ceil((maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24));

  // 计算每个任务的像素位置和宽度
  const getTaskStyle = (task: GanttTask) => {
    const daysFromStart = Math.ceil(
      (task.start.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    const taskDuration = Math.ceil(
      (task.end.getTime() - task.start.getTime()) / (1000 * 60 * 60 * 24)
    );
    const leftPercent = (daysFromStart / totalDays) * 100;
    const widthPercent = (taskDuration / totalDays) * 100;

    const colors: Record<string, string> = {
      project: '#3b82f6',
      phase: '#8b5cf6',
      task: '#10b981',
      milestone: '#f59e0b',
    };

    const statusColors: Record<string, string> = {
      completed: '#10b981',
      active: '#3b82f6',
      planning: '#6b7280',
      delayed: '#ef4444',
    };

    return {
      left: `${leftPercent}%`,
      width: `${widthPercent}%`,
      backgroundColor: statusColors[task.status] || colors[task.type] || '#6b7280',
    };
  };

  // 生成日期标签
  const generateDateLabels = () => {
    const labels: { date: Date; label: string }[] = [];
    const interval = Math.max(1, Math.floor(totalDays / 10));

    for (let i = 0; i <= totalDays; i += interval) {
      const date = new Date(minDate.getTime() + i * 24 * 60 * 60 * 1000);
      labels.push({
        date,
        label: `${date.getMonth() + 1}/${date.getDate()}`,
      });
    }
    return labels;
  };

  const dateLabels = generateDateLabels();

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
      <div className="overflow-x-auto">
        <div className="min-w-full" style={{ height: `${height}px` }}>
          {/* 日期轴 */}
          <div className="relative border-b border-gray-200 mb-4" style={{ height: '40px' }}>
            {dateLabels.map((label, idx) => (
              <div
                key={idx}
                className="absolute border-l border-gray-300"
                style={{
                  left: `${idx * (100 / (dateLabels.length - 1))}%`,
                  height: '100%',
                  paddingLeft: '4px',
                  fontSize: '12px',
                  color: '#6b7280',
                }}
              >
                {label.label}
              </div>
            ))}
          </div>

          {/* 任务条 */}
          <div className="relative" style={{ height: `${height - 60}px` }}>
            {tasks.map((task, idx) => {
              const style = getTaskStyle(task);
              return (
                <div
                  key={task.id}
                  className="absolute rounded cursor-pointer hover:opacity-80 transition-opacity"
                  style={{
                    ...style,
                    top: `${idx * 50}px`,
                    height: '36px',
                    lineHeight: '36px',
                    paddingLeft: '8px',
                    paddingRight: '8px',
                    color: 'white',
                    fontSize: '12px',
                    fontWeight: '500',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                  title={`${task.name} (${task.start.toLocaleDateString()} - ${task.end.toLocaleDateString()})`}
                >
                  <div className="flex items-center justify-between h-full">
                    <span className="truncate">{task.name}</span>
                    {task.progress > 0 && (
                      <div className="ml-2 flex-1 bg-white bg-opacity-30 rounded h-2">
                        <div
                          className="bg-white h-2 rounded"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 图例 */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-blue-500"></div>
          <span>进行中</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-500"></div>
          <span>已完成</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gray-500"></div>
          <span>规划中</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-500"></div>
          <span>已延迟</span>
        </div>
      </div>
    </div>
  );
};
