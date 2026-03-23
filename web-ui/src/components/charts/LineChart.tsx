'use client';

import React from 'react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface LineChartProps {
  title?: string;
  data: any[];
  dataKey?: string;
  xKey?: string;
  height?: number;
}

export const LineChart: React.FC<LineChartProps> = ({
  title,
  data,
  dataKey = 'value',
  xKey = 'name',
  height = 300,
}) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div>暂无数据</div>
      </div>
    );
  }

  return (
    <div>
      {title && <h3 style={{ marginBottom: '16px' }}>{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey={dataKey} stroke="#8884d8" strokeWidth={2} />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};
