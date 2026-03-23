'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/UI/Card';
import { getAccessToken } from '@/lib/auth';

interface PerformanceChartsProps {
  timeRange: string;
}

interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor: string;
    backgroundColor: string;
  }>;
}

export function PerformanceCharts({ timeRange }: PerformanceChartsProps) {
  const [queryTimeData, setQueryTimeData] = useState<ChartData | null>(null);
  const [connectionData, setConnectionData] = useState<ChartData | null>(null);

  useEffect(() => {
    fetchChartData();
  }, [timeRange]);

  const fetchChartData = async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error('未登录');
      }
      const response = await fetch(
        `/api/admin/database/performance/charts?timeRange=${timeRange}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setQueryTimeData(data.queryTime);
        setConnectionData(data.connections);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
    }
  };

  // 简化的图表组件（实际应该使用Chart.js或Recharts）
  const renderChart = (title: string, data: ChartData | null, color: string) => {
    if (!data || data.labels.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
          暂无数据
        </div>
      );
    }

    const maxValue = Math.max(...data.datasets[0].data, 1);
    const minValue = Math.min(...data.datasets[0].data, 0);

    return (
      <div className="h-64 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            最大值: {maxValue.toFixed(2)} | 最小值: {minValue.toFixed(2)}
          </div>
        </div>
        <div className="relative h-full">
          <svg className="w-full h-full">
            <defs>
              <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                <stop offset="100%" stopColor={color} stopOpacity="0.05" />
              </linearGradient>
            </defs>
            {/* 简单的折线图绘制 */}
            <polyline
              points={data.datasets[0].data
                .map(
                  (value, index) =>
                    `${(index / (data.labels.length - 1)) * 100},${
                      100 - ((value - minValue) / (maxValue - minValue)) * 80
                    }`
                )
                .join(' ')}
              fill="none"
              stroke={color}
              strokeWidth="2"
            />
            <polygon
              points={`0,100 ${data.datasets[0].data
                .map(
                  (value, index) =>
                    `${(index / (data.labels.length - 1)) * 100},${
                      100 - ((value - minValue) / (maxValue - minValue)) * 80
                    }`
                )
                .join(' ')} 100,100`}
              fill={`url(#gradient-${title})`}
            />
          </svg>
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="p-6">{renderChart('查询时间趋势', queryTimeData, '#3B82F6')}</Card>
      <Card className="p-6">{renderChart('连接数趋势', connectionData, '#10B981')}</Card>
    </div>
  );
}
