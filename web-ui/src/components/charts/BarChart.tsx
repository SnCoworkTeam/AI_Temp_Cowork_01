'use client';

import React from 'react';
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface BarChartProps {
  title?: string;
  data: any[];
  dataKey?: string;
  xKey?: string;
  height?: number;
}

export const BarChart: React.FC<BarChartProps> = ({
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
        <RechartsBarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey={dataKey} fill="#8884d8" />
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
};
