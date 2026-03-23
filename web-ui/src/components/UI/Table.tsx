'use client';

import { ReactNode } from 'react';

interface TableProps {
  children: ReactNode;
  className?: string;
}

interface TableHeaderProps {
  children: ReactNode;
  className?: string;
}

interface TableBodyProps {
  children: ReactNode;
  className?: string;
}

interface TableRowProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  hover?: boolean;
}

interface TableHeadProps {
  children: ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
}

interface TableCellProps {
  children: ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
  colSpan?: number;
}

export function Table({ children, className = '' }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table
        className={`
          w-full border-collapse
          ${className}
        `}
        role="table"
      >
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ children, className = '' }: TableHeaderProps) {
  return (
    <thead
      className={`
        bg-muted
        ${className}
      `}
    >
      {children}
    </thead>
  );
}

export function TableBody({ children, className = '' }: TableBodyProps) {
  return <tbody className={className}>{children}</tbody>;
}

export function TableRow({ children, className = '', onClick, hover = true }: TableRowProps) {
  return (
    <tr
      className={`
        border-b border-border
        ${hover && onClick ? 'cursor-pointer hover:bg-accent' : ''}
        ${hover && !onClick ? 'hover:bg-accent/50' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

export function TableHead({ children, className = '', align = 'left' }: TableHeadProps) {
  const alignClasses = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  return (
    <th
      className={`
        px-4 py-3 text-sm font-semibold text-foreground
        ${alignClasses[align]}
        ${className}
      `}
    >
      {children}
    </th>
  );
}

export function TableCell({ children, className = '', align = 'left', colSpan }: TableCellProps) {
  const alignClasses = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  return (
    <td
      className={`
        px-4 py-3 text-sm text-foreground
        ${alignClasses[align]}
        ${className}
      `}
      colSpan={colSpan}
    >
      {children}
    </td>
  );
}
