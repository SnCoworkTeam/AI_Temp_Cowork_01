'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  ThemeMode,
  Theme,
  getEffectiveTheme,
  applyTheme,
  getSystemTheme,
  lightTheme,
  darkTheme,
} from '@/styles/theme';

interface ThemeContextType {
  theme: Theme;
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') return 'system';
    const stored = localStorage.getItem('theme-mode') as ThemeMode | null;
    return stored || 'system';
  });

  const [theme, setTheme] = useState<Theme>(() => {
    const effectiveTheme = getEffectiveTheme(mode);
    return effectiveTheme === 'dark' ? darkTheme : lightTheme;
  });

  // 应用主题
  useEffect(() => {
    const effectiveTheme = getEffectiveTheme(mode);
    const newTheme = effectiveTheme === 'dark' ? darkTheme : lightTheme;

    setTheme(newTheme);
    applyTheme(newTheme);
  }, [mode]);

  // 监听系统主题变化
  useEffect(() => {
    if (mode !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      const effectiveTheme = getEffectiveTheme('system');
      const newTheme = effectiveTheme === 'dark' ? darkTheme : lightTheme;
      setTheme(newTheme);
      applyTheme(newTheme);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [mode]);

  // 保存主题模式到localStorage
  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
    localStorage.setItem('theme-mode', newMode);
  }, []);

  // 切换主题（light <-> dark）
  const toggleTheme = useCallback(() => {
    const currentEffective = getEffectiveTheme(mode);
    const newMode = currentEffective === 'dark' ? 'light' : 'dark';
    setMode(newMode);
  }, [mode, setMode]);

  return (
    <ThemeContext.Provider value={{ theme, mode, setMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeContext() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  return context;
}
