'use client';

import React from 'react';
import {
  Brain,
  Search,
  Palette,
  CheckCircle2,
  Settings,
  Bot,
  Check,
  X,
  RefreshCw,
  Sparkles,
  Layers,
  Zap,
  FileText,
  Loader2,
} from 'lucide-react';

interface IconProps {
  className?: string;
  size?: number;
}

export const ThinkingIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Brain className={`${className} text-blue-500`} size={size} />
);

export const SearchIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Search className={`${className} text-blue-500`} size={size} />
);

export const DesignIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Palette className={`${className} text-blue-500`} size={size} />
);

export const CheckIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <CheckCircle2 className={`${className} text-green-500`} size={size} />
);

export const ExecuteIcon = ({
  className = 'w-4 h-4',
  size = 16,
  animate = false,
}: IconProps & { animate?: boolean }) => (
  <Settings
    className={`${className} text-green-500 ${animate ? 'animate-spin' : ''}`}
    size={size}
  />
);

export const AgentIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Bot className={`${className} text-green-500`} size={size} />
);

export const SuccessIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Check className={`${className} text-green-500`} size={size} />
);

export const ErrorIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <X className={`${className} text-red-500`} size={size} />
);

export const SynthIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <RefreshCw className={`${className} text-green-500 animate-spin`} size={size} />
);

export const SparkleIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Sparkles className={`${className} text-blue-500`} size={size} />
);

export const LayerIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Layers className={`${className} text-green-500`} size={size} />
);

export const ZapIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Zap className={`${className} text-yellow-500`} size={size} />
);

export const DocumentIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <FileText className={`${className} text-gray-500`} size={size} />
);

export const LoadingIcon = ({ className = 'w-4 h-4', size = 16 }: IconProps) => (
  <Loader2 className={`${className} text-blue-500 animate-spin`} size={size} />
);
