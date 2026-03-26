'use client';

import { AlertCircle, X, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import { useState, useEffect } from 'react';

export type MessageType = 'error' | 'success' | 'info' | 'warning';

interface ErrorMessageProps {
  message: string | null;
  type?: MessageType;
  onClose?: () => void;
  autoClose?: boolean | number; // 可以是布尔值或毫秒数
  className?: string;
}

export default function ErrorMessage({
  message,
  type = 'error',
  onClose,
  autoClose = false,
  className = '',
}: ErrorMessageProps) {
  const [visible, setVisible] = useState(!!message);

  useEffect(() => {
    setVisible(!!message);
    if (autoClose && message) {
      const delay = typeof autoClose === 'number' ? autoClose : 5000;
      const timer = setTimeout(() => {
        setVisible(false);
        if (onClose) {
          onClose();
        }
      }, delay);
      return () => clearTimeout(timer);
    }
  }, [message, autoClose, onClose]);

  if (!message || !visible) return null;

  const typeConfig = {
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      icon: AlertCircle,
      iconColor: 'text-red-600',
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      icon: CheckCircle,
      iconColor: 'text-green-600',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      icon: Info,
      iconColor: 'text-blue-600',
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      icon: AlertTriangle,
      iconColor: 'text-yellow-600',
    },
  };

  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <div
      className={`${config.bg} ${config.border} border rounded-lg p-4 mb-4 ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${config.iconColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <p className={`text-sm ${config.text} font-medium`}>{message}</p>
        </div>
        {onClose && (
          <button
            onClick={() => {
              setVisible(false);
              onClose();
            }}
            className={`${config.text} hover:opacity-70 transition-opacity flex-shrink-0`}
            aria-label="关闭"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

