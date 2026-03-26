'use client';

import {
  ReactNode,
  FormHTMLAttributes,
  InputHTMLAttributes,
  LabelHTMLAttributes,
  TextareaHTMLAttributes,
  SelectHTMLAttributes,
} from 'react';

interface FormProps extends FormHTMLAttributes<HTMLFormElement> {
  children: ReactNode;
}

interface FormFieldProps {
  label?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

interface FormLabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

interface FormInputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

interface FormTextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

interface FormSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

interface FormErrorProps {
  children: ReactNode;
}

interface FormHintProps {
  children: ReactNode;
}

export function Form({ children, className = '', ...props }: FormProps) {
  return (
    <form className={className} {...props}>
      {children}
    </form>
  );
}

export function FormField({
  label,
  error,
  hint,
  required,
  children,
  className = '',
}: FormFieldProps) {
  return (
    <div className={`mb-4 ${className}`}>
      {label && <FormLabel required={required}>{label}</FormLabel>}
      {children}
      {error && <FormError>{error}</FormError>}
      {hint && !error && <FormHint>{hint}</FormHint>}
    </div>
  );
}

export function FormLabel({ children, required, className = '', ...props }: FormLabelProps) {
  return (
    <label
      className={`
        block text-sm font-medium text-foreground mb-1
        ${className}
      `}
      {...props}
    >
      {children}
      {required && <span className="text-destructive ml-1">*</span>}
    </label>
  );
}

export function FormInput({ error, className = '', ...props }: FormInputProps) {
  return (
    <input
      className={`
        w-full px-4 py-2
        border rounded-lg
        bg-input text-foreground
        focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
        disabled:opacity-50 disabled:cursor-not-allowed
        ${error ? 'border-destructive' : 'border-border'}
        ${className}
      `}
      aria-invalid={error ? 'true' : 'false'}
      {...props}
    />
  );
}

export function FormTextarea({ error, className = '', ...props }: FormTextareaProps) {
  return (
    <textarea
      className={`
        w-full px-4 py-2
        border rounded-lg
        bg-input text-foreground
        focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
        disabled:opacity-50 disabled:cursor-not-allowed
        resize-vertical
        ${error ? 'border-destructive' : 'border-border'}
        ${className}
      `}
      aria-invalid={error ? 'true' : 'false'}
      {...props}
    />
  );
}

export function FormSelect({ error, children, className = '', ...props }: FormSelectProps) {
  return (
    <select
      className={`
        w-full px-4 py-2
        border rounded-lg
        bg-input text-foreground
        focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
        disabled:opacity-50 disabled:cursor-not-allowed
        ${error ? 'border-destructive' : 'border-border'}
        ${className}
      `}
      aria-invalid={error ? 'true' : 'false'}
      {...props}
    >
      {children}
    </select>
  );
}

export function FormError({ children }: FormErrorProps) {
  return (
    <p className="mt-1 text-sm text-destructive" role="alert">
      {children}
    </p>
  );
}

export function FormHint({ children }: FormHintProps) {
  return <p className="mt-1 text-sm text-muted-foreground">{children}</p>;
}

export function FormActions({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`flex justify-end gap-3 mt-6 ${className}`}>{children}</div>;
}
