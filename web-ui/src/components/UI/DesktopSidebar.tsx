'use client';

import { ReactNode } from 'react';

interface DesktopSidebarProps {
  children: ReactNode;
  className?: string;
  width?: 'sm' | 'md' | 'lg' | 'xl';
}

const widthClasses = {
  sm: 'w-48',
  md: 'w-64',
  lg: 'w-72',
  xl: 'w-80',
};

export function DesktopSidebar({ children, className = '', width = 'md' }: DesktopSidebarProps) {
  return (
    <aside
      className={`
        hidden lg:block fixed inset-y-0 left-0 z-30
        ${widthClasses[width]}
        bg-white dark:bg-gray-900
        shadow-lg
        ${className}
      `}
      aria-label="侧边栏导航"
    >
      {children}
    </aside>
  );
}
