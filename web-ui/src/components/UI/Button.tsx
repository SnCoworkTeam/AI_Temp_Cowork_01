'use client';

import { ButtonHTMLAttributes, forwardRef } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | 'primary'
    | 'secondary'
    | 'outline'
    | 'ghost'
    | 'destructive'
    | 'success'
    | 'warning'
    | 'info';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      icon,
      iconPosition = 'left',
      children,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const baseClasses =
      'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const variantClasses = {
      primary: 'bg-primary text-white hover:bg-primary/90 focus:ring-primary',
      secondary: 'bg-secondary text-white hover:bg-secondary/90 focus:ring-secondary',
      outline: 'border-2 border-border bg-transparent hover:bg-accent focus:ring-primary',
      ghost: 'hover:bg-accent focus:ring-primary',
      destructive:
        'bg-destructive text-destructive-foreground hover:bg-destructive/90 focus:ring-destructive',
      success: 'bg-success text-success-foreground hover:bg-success/90 focus:ring-success',
      warning: 'bg-warning text-warning-foreground hover:bg-warning/90 focus:ring-warning',
      info: 'bg-info text-info-foreground hover:bg-info/90 focus:ring-info',
    };

    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    const iconSizeClasses = {
      sm: 'w-4 h-4',
      md: 'w-5 h-5',
      lg: 'w-6 h-6',
    };

    const classes = `
      ${baseClasses}
      ${variantClasses[variant]}
      ${sizeClasses[size]}
      ${fullWidth ? 'w-full' : ''}
      ${className}
    `
      .trim()
      .replace(/\s+/g, ' ');

    const iconElement = icon && <span className={iconSizeClasses[size]}>{icon}</span>;

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading && (
          <svg
            className={`animate-spin ${iconSizeClasses[size]} mr-2`}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!loading && iconPosition === 'left' && iconElement}
        {children && <span>{children}</span>}
        {!loading && iconPosition === 'right' && iconElement}
      </button>
    );
  }
);

Button.displayName = 'Button';
