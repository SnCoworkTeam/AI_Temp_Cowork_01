'use client';

import { ReactNode, useEffect } from 'react';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
}

export function MobileMenu({ isOpen, onClose, children, className = '' }: MobileMenuProps) {
  // 阻止背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return (
    <>
      {/* 遮罩层 */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* 菜单 */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-900
          shadow-lg transform transition-transform duration-300 ease-in-out
          lg:hidden
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          ${className}
        `}
        role="dialog"
        aria-modal="true"
        aria-label="移动端菜单"
      >
        {children}
      </div>
    </>
  );
}
