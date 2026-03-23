'use client';

import React from 'react';
import { Card } from 'antd';

interface StatCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'accent' | string;
  loading?: boolean;
  gradient?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  color = 'primary',
  loading = false,
  gradient = false,
}) => {
  // 颜色映射
  const colorMap: Record<string, { bg: string; text: string; border: string }> = {
    primary: {
      bg: 'bg-primary/10',
      text: 'text-primary',
      border: 'border-primary/20',
    },
    secondary: {
      bg: 'bg-secondary/10',
      text: 'text-secondary',
      border: 'border-secondary/20',
    },
    accent: {
      bg: 'bg-accent/10',
      text: 'text-accent',
      border: 'border-accent/20',
    },
  };

  const colorClasses =
    typeof color === 'string' && colorMap[color]
      ? colorMap[color]
      : { bg: 'bg-primary/10', text: 'text-primary', border: 'border-primary/20' };

  const gradientClass = gradient
    ? color === 'primary'
      ? 'gradient-primary'
      : color === 'secondary'
        ? 'gradient-secondary'
        : color === 'accent'
          ? 'gradient-accent'
          : 'gradient-primary'
    : '';

  const textColor = gradient ? 'text-white' : colorClasses.text;
  const bgColor = gradient ? '' : colorClasses.bg;
  const borderColor = gradient ? '' : colorClasses.border;

  return (
    <Card
      loading={loading}
      className={`
        card-elevated 
        ${bgColor} 
        ${borderColor} 
        ${gradientClass}
        border 
        rounded-lg
        animate-fade-in
        transition-all duration-300
      `}
      style={{
        borderRadius: '8px',
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className={`text-sm mb-2 ${gradient ? 'text-white/90' : 'text-mutedForeground'}`}>
            {title}
          </div>
          <div className={`text-3xl font-title font-bold ${textColor}`}>{value}</div>
        </div>
        {icon && <div className={`text-4xl ${textColor} opacity-80`}>{icon}</div>}
      </div>
    </Card>
  );
};
