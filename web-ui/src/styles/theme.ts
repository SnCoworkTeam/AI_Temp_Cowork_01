/**
 * 主题配置
 */
export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  foreground: string;
  muted: string;
  mutedForeground: string;
  border: string;
  input: string;
  ring: string;
  card: string;
  cardForeground: string;
  popover: string;
  popoverForeground: string;
  destructive: string;
  destructiveForeground: string;
  success: string;
  successForeground: string;
  warning: string;
  warningForeground: string;
  info: string;
  infoForeground: string;
}

export interface Theme {
  name: string;
  colors: ThemeColors;
}

export const lightTheme: Theme = {
  name: 'light',
  colors: {
    primary: '#2563eb', // 科技蓝 - 主色
    secondary: '#10b981', // 活力绿 - 辅色
    accent: '#f59e0b', // 警示黄 - 强调色
    background: '#ffffff',
    foreground: '#0f172a',
    muted: '#f1f5f9',
    mutedForeground: '#64748b',
    border: '#e2e8f0',
    input: '#ffffff',
    ring: '#2563eb',
    card: '#ffffff',
    cardForeground: '#0f172a',
    popover: '#ffffff',
    popoverForeground: '#0f172a',
    destructive: '#ef4444',
    destructiveForeground: '#ffffff',
    success: '#10b981',
    successForeground: '#ffffff',
    warning: '#f59e0b',
    warningForeground: '#ffffff',
    info: '#3b82f6',
    infoForeground: '#ffffff',
  },
};

export const darkTheme: Theme = {
  name: 'dark',
  colors: {
    primary: '#3b82f6', // 科技蓝（深色模式稍亮）
    secondary: '#10b981', // 活力绿 - 辅色
    accent: '#f59e0b', // 警示黄 - 强调色
    background: '#0f172a',
    foreground: '#f8fafc',
    muted: '#1e293b',
    mutedForeground: '#94a3b8',
    border: '#334155',
    input: '#1e293b',
    ring: '#3b82f6',
    card: '#1e293b',
    cardForeground: '#f8fafc',
    popover: '#1e293b',
    popoverForeground: '#f8fafc',
    destructive: '#ef4444',
    destructiveForeground: '#ffffff',
    success: '#10b981',
    successForeground: '#ffffff',
    warning: '#f59e0b',
    warningForeground: '#ffffff',
    info: '#3b82f6',
    infoForeground: '#ffffff',
  },
};

export const themes: Record<string, Theme> = {
  light: lightTheme,
  dark: darkTheme,
};

/**
 * 获取系统偏好主题
 */
export function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * 应用主题到DOM
 */
export function applyTheme(theme: Theme) {
  if (typeof document === 'undefined') return;

  const root = document.documentElement;

  // 设置CSS变量
  Object.entries(theme.colors).forEach(([key, value]) => {
    root.style.setProperty(`--color-${key}`, value);
  });

  // 设置类名
  if (theme.name === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

/**
 * 获取有效主题（处理system模式）
 */
export function getEffectiveTheme(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') {
    return getSystemTheme();
  }
  return mode;
}
