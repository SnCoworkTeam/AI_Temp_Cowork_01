'use client';

import { useThemeContext } from '@/contexts/ThemeContext';
import { ThemeMode } from '@/styles/theme';

/**
 * 主题切换Hook
 *
 * @example
 * ```tsx
 * const { theme, mode, setMode, toggleTheme } = useTheme()
 *
 * // 切换主题
 * <button onClick={toggleTheme}>切换主题</button>
 *
 * // 设置特定主题
 * <button onClick={() => setMode('dark')}>深色模式</button>
 * ```
 */
export function useTheme() {
  return useThemeContext();
}

/**
 * 检查当前是否为深色模式
 */
export function useIsDark() {
  const { theme } = useTheme();
  return theme.name === 'dark';
}

/**
 * 主题模式切换Hook（简化版）
 */
export function useThemeToggle() {
  const { toggleTheme, mode, setMode } = useTheme();

  return {
    toggle: toggleTheme,
    mode,
    setMode,
  };
}
